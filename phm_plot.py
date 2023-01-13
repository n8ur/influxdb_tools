#! /usr/bin/env -S python3      # took away -u to see if it helps

# phm_plot.py v.20230113.1
# copyright 2023 John Ackermann N8UR jra@febo.com
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# This is an example of plotting many fields from a file created
# by jra's influx_query.py program.  It creates a single figure
# containing the desired number of subplots in a row, column format.
# Each subplot can have up to three separately scaled Y axes.  The
# x axis is the timestamp from the input file.
#
# Most variables are set at top of program, but you may well want to
# tweak formatting down in the guts of the program.
#
# The input file can have fields delimited as specified, and assumes
# the first line is a list of all the fields with the same delimiter
# between them.
#
# ASSUMPTION: there is a field called 'iso' that contains
# an iso8601 timestamp for each line, and another called 'unix' that
# contains a Unix timestamp for each line as in the output file
# created in the influx_query.py program.  If desired, this
# could be changed in the code below without too much trouble
# 
# Usage: phm_plot.py <input_file>
# Generates <input_file_basename>.png

import os
import sys
from datetime import datetime
from astropy.io import ascii
from astropy.table import Table
import astropy.units as u
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib.dates as mdates

# delimiter of input data file
input_delimiter = '\t'

# Show plot on display; make output PNG
show_disp = True ; make_png = True

# Plot will have subplots in row, column format
# with shared x axis as timestamp
num_rows = 4 ; num_cols = 3

# These are nominally inches, but that depends on
# resolution.  PNG size seems to be these values x 100 pixels
# Tinker until it looks OK.
fig_width = 16 ; fig_height = 9

# Borders to leave around subplots 0,0 is bottom
# left; 1,1 is top right.
b_left = 0.05 ; b_bottom = 0.075 ; b_right = 0.9 ; b_top = 0.925

# horiz_space is minimum space between subplots
horiz_space = 0.4

# this sets how far right to place 3rd axis label/ticks
third_axis_placement = 1.225
# Title at top of figure
suptitle = "VCH-1008 #107"

# List of params for each subplot. Subplots will be displayed 
# in order included below, starting from top left and finishing
# at bottom right.  Last plots will be empty if no line is present
# for them here.  Color order is red, blue, green.  This allows for
# up to 3 y axes per subplot, but could be expanded.  Enter "None"
# for field and label of unused axes.
#
# List items are: 
# [ title, y1, ylabel1, y2, ylabel2, y3, ylabel3 
# y1min, y1max, y2min, y2max, y3min, y3max ]
#
# title and y1 are the minimum required for each plot; set unused
# items to 'None'.  The last six items set Y axis ranges.  Set to 
# 'None' for autoscale.
subs = [
    ['Ion Pump','ion_current','Current','ion_volts','Volts',None,None,
        None,None,None,None,None,None],
    ['2nd Harmonic','2nd_harm',None,None,None,None,None,
        None,None,None,None,None,None],
    ['DACs','resonator_dac','Resonator','xtal_dac','XTAL','synth_dac','Synth',
        None,None,None,None,675,700],
    ['HFO','hfo_current','Current','hfo_volts','Volts',None,None,
        None,None,None,None,None,None],
    ['Temperatures','afc_tmp','AFC Degrees','rtd_temp',
        'Rack Degrees',None,None,
        None,None,None,None,None,None],
    ['Purifier','pur_current','Current','pur_volts','Volts',None,None,
        None,None,None,None,None,None],
    ['Cavity Base','cav_base_mistmatch','Mismatch','cav_base_pwr',
        'Power',None,None,
        None,None,None,None,None,None],
    ['Cavity Side','cav_side_mismatch','Mismatch','cav_side_pwr',
        'Power',None,None,
        None,None,None,None,None,None],
    ['Hydrogen Source','h_src_mismatch','Mismatch','h_src_pwr',
        'Power',None,None,
        None,None,None,None,None,None],
    ['Voltages','int+15vdc','+15 Volts','int+5vdc','+5 Volts',None,None,
        14.8,15.2,4.9,5.1,None,None],
    ['Voltages','int-15vdc','-15 Volts','int_27vdc','+27 Volts',None,None,
        -15.7,-14.3,27.5,28.5,None,None],
    ]


# Some global figure properties
mpl.rcParams['axes.grid']=True
mpl.rcParams['axes.grid.axis']='x'
mpl.rcParams['grid.color']='grey'
mpl.rcParams['grid.alpha']=0.5
mpl.rcParams['figure.autolayout']=False
mpl.rcParams['lines.linewidth'] = 0.6

############################### CODE BEGINS #############################

# Read in columnular data with tab separated values
# NOTE: I haven't figured out how to get astropy tables to read
# field names from a line beginning with '#'
t = Table.read(sys.argv[1],format='ascii',delimiter=input_delimiter)

# Make X axis based on timestamps
start_iso = t[0]['iso']
end_iso = t[len(t)-1]['iso']
dates=[datetime.fromtimestamp(ts) for ts in t['unix']]
x=mdates.date2num(dates)
subtitle = "Data starts " + start_iso + " and ends " + end_iso

# set up figures
fig, axes = plt.subplots(nrows=num_rows, ncols=num_cols, 
    figsize=(fig_width, fig_height),sharex='col')

fig.subplots_adjust(b_left,b_bottom,b_right,b_top,horiz_space)

# Position, size, color of title at top
fig.suptitle(suptitle,size='xx-large',weight='bold',x=0.5,y=0.98)

# Line showing date range at bottom
fig.text(0.5,0.0225,subtitle,horizontalalignment='center',
    size='large',weight='bold')
# Put date/time plotted at bottom right
now = "Created: " + datetime.utcnow().isoformat(timespec='seconds') + " UTC"
fig.text(0.9,0.01,now,horizontalalignment='right',
    size='medium')

for i, ax in enumerate(axes.flat):
    # only make as many subs as have data
    if i > len(subs) - 1:
        break
    if subs[i][0] != None:
        ax.set_title(subs[i][0])

    # there's always at least one y axis
    if subs[i][2] != None:
        ax.set_ylabel(subs[i][2],color='red')
    ax.tick_params(axis='y',colors='red')
    ax.ticklabel_format(useOffset=False,style='plain')
    # if we've set limits for the y axis
    if subs[i][7] != None and subs[i][8] != None:
        ax.set_ylim(subs[i][7],subs[i][8])
    ax.plot(x, t[subs[i][1]],color='red',zorder=0)

    # if there's a second y axis
    if subs[i][3] != None:
        axa = ax.twinx()
        if subs[i][4] != None:
            axa.set_ylabel(subs[i][4],color='blue')
        axa.tick_params(axis='y',colors='blue')
        axa.ticklabel_format(useOffset=False,style='plain')
        # if we've set limits for the y axis
        if subs[i][9] != None and subs[i][10] != None:
            axa.set_ylim(subs[i][9],subs[i][10])
        axa.plot(x, t[subs[i][3]],color='blue',zorder=5)

    # if there's a third y axis
    if subs[i][5] != None:
        axb = ax.twinx()
        if subs[i][6] != None:
            axb.set_ylabel(subs[i][6],color='green')
        axb.tick_params(axis='y',colors='green')
        axb.ticklabel_format(useOffset=False,style='plain')
        axb.spines.right.set_position(("axes", third_axis_placement))
        # if we've set limits for the y axis
        if subs[i][11] != None and subs[i][12] != None:
            axb.set_ylim(subs[i][11],subs[i][12])
        axb.plot(x, t[subs[i][5]],color='green',zorder=10)

# put x axis ticks at bottom of each column
for x in range(num_cols):
    axes[num_rows - 1,x].xaxis.set_major_formatter(mdates.DateFormatter('%d-%b'))

if make_png == True:
    pngout = os.path.basename(sys.argv[1]) + '.png'
    print("Saving to",pngout)
    plt.savefig(pngout,bbox_inches='tight')
    plt.savefig(pngout)
if show_disp == True:
    plt.show()

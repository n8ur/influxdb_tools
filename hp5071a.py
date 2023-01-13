#!/usr/bin/env python3

# hp5071a.py v.20230110.1
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

# This program is called by logger_1m.sh to query an HP5071A Cesium
# frequency standard for operating parameters.

import sys
import signal
import socket
import serial
import time
from datetime import datetime
from datetime import timezone

from influxdb_client import InfluxDBClient

port = sys.argv[1]

cmds = ['DIAG:CONT:STATE?','DIAG:CURR:BEAM?','DIAG:CURR:CFIELD?',
        'DIAG:CURR:PUMP?','DIAG:GAIN?','DIAG:RFAMPLITUDE?',
        'DIAG:STAT:GLOB?','DIAG:STAT:SUPP?','DIAG:TEMP?',
        'DIAG:VOLT:COV?','DIAG:VOLT:EMUL?','DIAG:VOLT:HWI?',
        'DIAG:VOLT:MSP?','DIAG:VOLT:PLL?','DIAG:VOLT:ROSC?',
        'DIAG:VOLT:SUPP?' ]

fields = ['State','Beam_Current','C-Field',
        'Ion_Pump','Gain','RF_Amp_#1','RF_Amp_#2',
        'Status','Pwr_Supply','Ambient_Temp',
        'CBT_Oven','EMult','HW_Ionizer','Mass_Spectrometer',
        'PLL_1','PLL_2','PLL_3','PLL_4','Osc_Mon','PS_+5',
        'PS_+12','PS_-12']

results = []
# these are commands that return a single float
float_results = [1,2,3,4,8,9,10,11,12,14]
# these are commands that return a string
string_results = [0,6,7]

### GET DATA ###
try:
    ser = serial.Serial(port, 9600, timeout=0.5)
except:
    print("hp5071a: couldn't open serial port ", port)
    exit()

for i,x in enumerate(cmds):
    c = (x + '\r\n').encode()
    try:
        ser.write(c)
    except serial.SerialTimeoutException:
        print("hp5071a: timeout while sending command",x)
        exit()

    timeout = time.time() + 5 # wait up to 5 seconds for response
    while True:
        while not ser.inWaiting():
            if time.time() > timeout:
                print("hp5071a: didn't get response")
                exit()
        tmp = []
        tmp = ser.read(255).split()

        if i == 0:  # continuous operation status -- OFF/ENA/ON
            results.append("\"" + tmp[1].decode() +"\"")
        if i in float_results:      # all the commands returning single float
            results.append(float(tmp[1]))
        if i == 5:      # output voltage; two values
            x,y = tmp[1].decode().split(',')
            results.append(float(x))
            results.append(float(y))
        if i == 6:      # Status -- two word string 
            x = tmp[1].decode().replace('"','')
            y = tmp[2].decode().replace('"','')
            results.append("\"" +x + "_" + y + "\"")
        if i == 7: results.append("\"" + tmp[1].decode() + "\"") 
        if i == 13: # PLL voltages
            a,b,c,d = tmp[1].decode().split(',')
            results.append(float(a))
            results.append(float(b))
            results.append(float(c))
            results.append(float(d))
        if i == 15:     # Power supplies
            # manual says 4 values, but only 3 returned
            a,b,c = tmp[1].decode().split(',')
            results.append(float(a))
            results.append(float(b))
            results.append(float(c))

        break
ser.close()

#for x,y in enumerate(fields):
#        print(y," ",results[x])

### Create messages for telegraf ###
#The file handler for the Telegraf process.
telegraf_socket = "/var/telegraf/telegraf.sock"

# Connection to Telegraf, over a network socket.
with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as sock:
    sock.settimeout(5)
    attempts = 0
    while attempts < 3:
        try:
            sock.connect(telegraf_socket)
            print("hp5071a: connected to telegraf socket")
        except socket.error as e:
            print("hp5071a: couldn't connect to telegraf!")
            print("Try again in 3 seconds")
            print(e)
            attempts = attempts + 1
            time.sleep(3)
            break

        print("hp5071a: sending to telegraf socket")
        for idx,cmd in enumerate(fields):
            message = "hp5071a,location=clockroom " + \
            cmd + "=" + str(results[idx]) + " " + \
            str(time.time_ns()) + '\n'
            try:
                sock.send(message.encode())
                attempts = 3
            except socket.error as e:
                print("hp5071a: couldn't send to socket; wait and try again")
                print(e)
                attempts = attempts + 1
                time.sleep(3)
                break
        try:
            sock.close()
            attempts = 3
        except socket.error as e:
            print("hp5071a: couldn't close socket!")
            print(e)
            break
quit()

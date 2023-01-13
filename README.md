influx_tools version 20230113.1
Copyright 2023 John Ackermann N8UR jra@febo.com
Licensed under GPL v3 or later (see terms in each file).

These are some tools to log parameters reported from frequency 
standards and other sensors into an InfluxDB v2 database, and to 
pull data for instruments from that database, convert it into a tab 
separated value file, and plot many params from that file to a single 
figure containing up to 12 graphs using matplotlib.

These tools work, for a definition of "work" that means I got them 
to run in my environment to do more or less what I wanted them to.
They will certainly need to be customized for any other application.

The storage flow is that a systemd service runs the Influx "telegraf"
program that listens on a socket for data and writes what it hears to
the database.

A systemd timer service runs logger_1m.sh every minute.  That script
runs a separate python script to grab data via ethernet or USB or whatever
from each monitored device and write it to the telegraf socket.

InfluxDB data is not stored in a traditional many-fields-per-time-interval
format, so the influx_query.py program will read fields from the database
for a specified time range and use the "Flux" query language to
perform a pivot function that turns the results into a columnar format
table.  It takes a start and stop time in ISO8601 format, and a string
for the number of readings to aggregate (average) for each output line.
This can be used to thin down the data.  If you want 1:1 correspondence,
set to '1m'.  (An advantage of calling the aggregation function even
when not reducing data is that it results in a timestamp with seconds rather
than nanoseconds precision.  That avoids problems matching up data fields
tiny timestamp differences.  This could of course be done in the Python
code, but the aggregate function is a convenient way to handle it.)

phm_plot.py has turned into a kind of neat tool to put multiple
subplots onto a single output figure.  It will require customization
for your application, but I tried to put all the critical settings
at the top, and document things fairly well. 'tsv_test.dat.png' is
an example output image.

Note that these tools are written to work with the Flux query API used
in InfluxDB version 2.  I don't think they will work with version 1.8
or earlier.

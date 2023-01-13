#! /usr/bin/env -S python3

# influx_query.py  v.20230110.1
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

# This is an unfinished but workable program to query an InfluxDB v2
# database and return date in column format in timestamp order.
# This relies on the Flux API and therefore I don't think it will work
# with InfluxDB v1.8 or earlier.
# Output is tab separated.
#
# NOTE: no attempt is made to format the output data, so sometimes
# there are floats with ridiculous numbers of decimal places.  I
# don't think there's a universal answer for this because some data
# is in fact many decimal places deep so we don't want to lose precision
# for them.  It's probably better to deal with rounding after this
# processing is complete.


import codecs
from datetime import datetime
import os
import re
import sys
# pip3 install influxdb-client
from influxdb_client import InfluxDBClient

# ISO8601 format datetime
start = str(sys.argv[1])
stop = str(sys.argv[2])

# InfluxDB wants Zulu at end of date (RFC3339)
if not start[-1] == 'Z':
   start = start + 'Z'
if not stop[-1] == 'Z':
   stop = stop + 'Z'

# reduce data by aggregating this number of readings
# needs to be string with m,h,d, etc. e.g. '5m'
agg_val = str(sys.argv[3])

# adjust for local environment
url = 'your_url'
org = 'your_org'
bucket = 'your_bucket'
token = 'your_token'

# Output file name is built from bucket, start, stop, aggregation 
# value, with ISO8601 dates truncated to the minute and without Z,
# just to shorten things up a bit
outfile = bucket + '_' + start[:16].replace(':','')  + \
        '_' + stop[:16].replace(':','') + '_' + agg_val + '.dat'
# open output file
try:
    outf = open(outfile,'w')
except:
    print("Couldn't open output file",outfile)
    sys.exit()
print("Output is in",outfile)

# This is a list of all the fields you want to get from the
# database.  This list isn't actually used in the program, but
# is awfully handy to have for reference.
# Timestamp field is implied

full_field_list = [ 'field1','field2','field3','etc' ]

# These are the fields to log.  We assume all fields have unique
# names, so don't need to deal with the measurement name.  Instead,
# we build a regex that the database can match field names agains
# Timestamp field is implied

fields = [ 'field1','field2', ]

# Convert list 'fields' into a regex with values OR'd
# I *think* this needs to be in plain text, not compiled
# into a perl regex
fields_re = '|'.join(fields)
# '+' sign in Flux queries need to be escaped.  Are there others?
fields_re = fields_re.replace('+','\+')

# Pattern to semi-reliably detect an ISO8601 date
iso = re.compile(r'^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d')

# Build pieces of the query string.  Sort by time as that's
# not guarantted.  Always include the aggregate function even
# if not needed, as it strips off the fractional part of the
# ISO8601 seconds.  Drop the _start and _stop columns as they're
# not useful here.  Add the group and pivot functions to turn results
# into a column-oriented set of data records
from_bucket = 'from(bucket: "' + bucket + '")'  # need to add the '"'s
time_range = '|> range(start: ' + start + ', stop: ' + stop + ')'
field_match = '|> filter(fn: (r) => r["_field"] =~ /^(' + fields_re + ')$/)'
sort = '|> sort(columns: ["_time"])'
aggregate = '|> aggregateWindow(every: ' + str(agg_val) + ', fn: mean)'
drop = '|> drop(columns: ["_start","_stop"])'
group = '|> group() '
pivot = \
    '|> pivot(rowKey: ["_time"], columnKey: ["_field"],valueColumn: "_value")'

# Put 'em together
my_query = from_bucket + time_range + field_match + sort + aggregate + \
    drop + group + pivot

# Note the weird timeout value.  This needs to be pretty
# long for big queries
with InfluxDBClient(url=url,token=token,org=org,timeout=600_000) as client:
    query_api = client.query_api()
    csv_result = query_api.query_csv(my_query)
    for record in csv_result:
        if record == []:        # empty record
            continue
        if str(record[0]).startswith('#'):  # get rid of comments
            continue
        try:
            record = record[3:]     # first 3 fields aren't useful
        except:
            continue
        try:
            record[0] = record[0].rstrip('Z')    # get rid of trailing Z
        except:
            continue
        # The order of the columns in the returned data might not
        # be predictable, but the field names are contained in the
        # first row that doesn't start with '#'.  Assumes the first
        # field of header names starts with _time and all following
        # rows are iso 8601 strings.  Convert the ISO timestamp into
        # unix time for convenience (both are included in output).
        if record[0] == '_time':
            # drop the _time field
            field_list = record[1:]
            # insert iso and unix time fields
            field_list.insert(0,'unix')
            field_list.insert(0,'iso')
            f = '\t'.join(field_list)
            # print metadata
            outf.write("# Query run on bucket {} at {}\n". \
                format(bucket, \
                datetime.utcnow().isoformat(timespec='seconds',sep='T')))
            outf.write("# Records start at {} and end at {}\n". \
                format(start.rstrip('Z'),stop.rstrip('Z')))
            outf.write("# Field names:\n")
            # print the list of fields.  note no "#" at
            # beginning because astropy won't read them
            outf.write(f + '\n')
        try:
            unix_time = str(int(datetime.fromisoformat(record[0]).timestamp()))
            record.insert(1,unix_time)
        except:
            continue
        line = '\t'.join(record).rstrip('\r')
        outf.write(line + '\n')
outf.close()

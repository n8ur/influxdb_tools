#!/usr/bin/env python3

# maser_logger.py v.20230110.1
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

# This program is called by logger_1m.sh to query a VCH-1008 passive
# hydrogen maser for operating parameters.

import sys
import signal
import socket
import time
from datetime import datetime
from influxdb_client import InfluxDBClient
from maser_funcs import *

telegraf_socket = "/var/telegraf/telegraf.sock"

host = "maser.febo.com"
port = 5000

logfile = "/home/jra/maser_log.dat"
measure_name = "phm107"
location = "clockroom"

# in the below, make sure that each list is the same
# length, and that the query, function, and message
# line up

# these are the queries we send to the maser
query = ["?RSS","?PWR","?KVD","?FLL","?THR","?NAVSTAT", \
        "?PPSMEA","?ESYNSIG","?SYNTH","?STAT"]

# these are the functions that process the return of each query
# into the proper format to ship to telegraf
msg_funcs = [ rss_func, pwr_func, kvd_func, fll_func, thr_func, \
        navstat_func, ppsmea_func, esynsig_func, synth_func, stat_func ]

num_queries = len(query)      
fields = []
msg = []

def get_data(client, query):
    client.send(query.encode())
    from_server = client.recv(255)
    from_server = from_server[:-1]      # strip trailing null byte
    fields = from_server.decode('utf8').split()
    return fields

def worker(num_tries):
    attempts = 0
    got_data = False
    # create socket with 5 second timeout
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.settimeout(5)

    # check and turn on TCP Keepalive
    x = client.getsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE)
    if (x == 0):
        x = client.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)

    # now connect to the server
    while attempts < num_tries:
        try:
            print("maser_logger: connecting to " + host + " on port " +  str(port))
            client.connect((host,port))
            print("maser_logger: connected")
            break
        except socket.error as e:
            print("maser_logger: socket connect failed! Try again in 3 seconds")
            print("maser_logger: ",e)
            attempts = attempts + 1
            time.sleep(5.0)
            continue

    attempts = 0
    while attempts <  num_tries and got_data == False:
        try:
            t = str(time.time_ns())
            for x in range(0, num_queries - 1):
                fields = get_data(client, query[x])
                tmp_msg = msg_funcs[x](t, fields)
                msg.append(measure_name + ",location=" + location + tmp_msg)
            got_data = True
            print("maser_logger: got data from maser")
        except socket.timeout as e:
            print("maser_logger: socket timeout! Try again in 3 seconds")
            print("maser_logger: ",e)
            attempts = attempts + 1
            time.sleep(3)
        except Exception as e:
            print("maser_logger: other error; exit and try again")
            print("maser_logger: ",e)
            attempts = attempts + 1
        try:
            sock.close()
        except:
            pass

##### END OF DATA COLLECTION #####

##### BEGINNING OF DATA SEND TO TELEGRAF #####

# Connection to Telegraf, over a network socket.
    attempts = 0
    while attempts < num_tries and got_data == True:
        with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as sock:
            try:
                print("maser_logger: trying to connect to telegraf socket")
                sock.connect(telegraf_socket)
                sock.settimeout(5.0)
                print("maser_logger: connected")
            except socket.error as e:
                print("maser_logger: connect failed! Try again in 3 seconds")
                print("maser_logger: ",e)
                attempts = attempts + 1
                time.sleep(3.0)
                break
            for x in range(len(msg)):
                try:
                    sock.send(msg[x].encode())
                    got_data = False
                except socket.timeout as e:
                    print("maser_logger: ",e)
                    attempts = attempts + 1
                    time.sleep(3)
                except Exception as e:
                    print("maser_logger: other error; exit and try again")
                    print("maser_logger: ",e)
                    attempts = attempts + 1
            print("maser_logger: sent messages to telegraf")
            try:
                sock.close()
            except:
                pass

    with open(logfile,'a') as f:
        try:
            for x in range(len(msg)):
                f.write(msg[x])
            f.close()
        except Exception as e:
            print("maser_logger: couldn't open log file ", logfile)
            print("maser_logger: " +e)
    quit()   

if __name__ == '__main__':
    worker(3)

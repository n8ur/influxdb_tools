#!/usr/bin/env python3
# therm_usb.py v.20230110.1
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

# This program is called by logger_1m.sh to query an Arduino via USB
# to gather data from a BME280 temp/humidity/pressure sensor and an
# RTD thermometer


import sys
import signal
import socket
import serial
import time
from datetime import datetime
from datetime import timezone

from influxdb_client import InfluxDBClient

port = sys.argv[1]

### GET DATA ###
try:
    ser = serial.Serial(port, 115200, timeout=0.5)
except:
    print("therm_usb: couldn't open serial port ", port)
    exit()

try:
    ser.write(b'D') # this can be anything but tilde (~) 
except serial.SerialTimeoutException:
    print("therm_usb: timeout while sending prompt")
    exit()

timeout = time.time() + 20 # wait up to 20 seconds for response
while True:
    while not ser.inWaiting():
        pass
    if time.time() > timeout:
        print("therm_usb: didn't get therm response")
        exit()
    from_sensor = ser.readline()
    break
ser.close()

fields = from_sensor.decode('utf8').split()
message =   "therm1" + \
    ",location=clockroom" + \
    " rtd_temp=" + str(fields[0]) + \
    ",bme_temp=" + str(fields[1]) + \
    ",pressure=" + str(fields[2]) + \
    ",humidity=" + str(fields[3]) + \
    " " + str(time.time_ns()) + \
    "\n"
#The file handler for the Telegraf process.
telegraf_socket = "/var/telegraf/telegraf.sock"

# Connection to Telegraf, over a network socket.
with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as sock:
    sock.settimeout(5)
    attempts = 0
    while attempts < 3:
        try:
            sock.connect(telegraf_socket)
            print("therm_usb: connected to telegraf socket")
        except socket.error as e:
            print("therm_usb: couldn't connect to telegraf!")
            print("Try again in 3 seconds")
            print(e)
            attempts = attempts + 1
            time.sleep(3)
            break
        try:
            print("therm_usb: sending to telegraf socket")
            sock.send(message.encode())
            attempts = 3
        except socket.error as e:
            print("therm_usb: couldn't send to socket; wait and try again")
            print(e)
            attempts = attempts + 1
            time.sleep(3)
            break
        try:
            sock.close()
            attempts = 3
        except socket.error as e:
            print("therm_usb: couldn't close socket!")
            print(e)
            break
quit()

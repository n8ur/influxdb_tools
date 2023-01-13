#!/bin/bash

echo "Running logger_1m..."
/usr/local/bin/therm_usb.py /dev/ttyACM0
/usr/local/bin/maser_logger.py
/usr/local/bin/hp5071a.py /dev/ttyUSB0
#/home/jra/maser_logger_local.py

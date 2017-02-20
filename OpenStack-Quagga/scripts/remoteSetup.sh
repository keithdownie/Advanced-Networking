#!/bin/bash

# Written by Keith Downie
#
# This script does the initial config setup for using Quagga

sudo mv ~/daemons /etc/quagga/daemons
touch /etc/quagga/ospfd.conf
touch /etc/quagga/zebra.conf
chown quagga.quaggavty /etc/quagga/*.conf
echo 'password zebra' > /etc/quagga/ospfd.conf
echo 'password zebra' > /etc/quagga/zebra.conf
echo 1 > /proc/sys/net/ipv4/ip_forward

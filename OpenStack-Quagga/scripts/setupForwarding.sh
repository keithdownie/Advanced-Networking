#!/bin/bash

# Written by Keith Downie
#
# Sets the intial topology using setupOSPF.py and setupHost.py

python setupOSPF.py R1 10
python setupOSPF.py R2 10
python setupOSPF.py R3 10
python setupHost.py HostA R1
python setupHost.py HostB R3

#!/bin/bash

# Written by Keith Downie
#
# Create the initial OpenStack topology using newRouter.sh

./newRouter.sh HostA net10 null False
./newRouter.sh HostB net13 null False
./newRouter.sh R1 net10 net11 True
./newRouter.sh R2 net11 net12 True
./newRouter.sh R3 net12 net13 True

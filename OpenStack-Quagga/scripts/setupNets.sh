#!/bin/bash

# Written by Keith Downie
#
# Creates the subnets for the OpenStack topology


python cleanupOpenstack.py
python setupNet.py "net10" "10"
python setupNet.py "net11" "11"
python setupNet.py "net12" "12"
python setupNet.py "net13" "13"
echo "Adding Public Key to Default Security Group"
nova keypair-add --pub_key cloud.key.pub cloud

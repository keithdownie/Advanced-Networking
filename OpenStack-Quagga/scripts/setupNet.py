#!/usr/bin/env python

# Written by Keith Downie
#
# Creates a single subnet on OpenStack with Neutron

from neutronclient.v2_0 import client
import os
import sys

def main():
	print "Starting Neutron Client..."
	# Get passed in arguments
	name = sys.argv[1]
	netSub = sys.argv[2]

	neutron = client.Client(username=os.environ['OS_USERNAME'], password=os.environ['OS_PASSWORD'], tenant_id=os.environ['OS_TENANT_ID'], auth_url=os.environ['OS_AUTH_URL'])

	print "Creating Net "+name
	ext = neutron.list_networks(name="ext-net")['networks'][0]
	# Build up new the topology
	# Create net
	net = neutron.create_network({'network':{'name':name, 'admin_state_up': True}})['network']
	# Create subnet
	snet = neutron.create_subnet({'subnet':{'network_id':net['id'], 'cidr':'10.0.'+netSub+'.0/24', 'ip_version':'4'}})['subnet']
	print "Creating Router to ext-net"
	# Create the router with a default gateway of ext-net
	router = neutron.create_router({'router':{'name':'router'+name, 'external_gateway_info':{'network_id':ext['id']}}})['router']
	# Assign the router to the net
	neutron.add_interface_router(router['id'], {'subnet_id':snet['id']})

if __name__ == "__main__":
	main()
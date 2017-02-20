#!/usr/bin/env python

# Written by Keith Downie
#
# Used for cleaning up the OpenStack experiment when it is finished.

from neutronclient.v2_0 import client
import os
import sys

def main():
	print "Starting Neutron Client..."
	neutron = client.Client(username=os.environ['OS_USERNAME'], password=os.environ['OS_PASSWORD'], tenant_id=os.environ['OS_TENANT_ID'], auth_url=os.environ['OS_AUTH_URL'])
	
	print "Cleaning Up Defualt OpenStack Networks and Routers"
	# Tear down default routers and networks
	router1 = neutron.list_routers(name="flat-lan-1-router")["routers"][0]
	router2 = neutron.list_routers(name="tun0-router")["routers"][0]
	
	print "Removing Gateways"
	# Remove the gateways from the router
	neutron.remove_gateway_router(router1["id"])
	neutron.remove_gateway_router(router2["id"])

	print "Deleting Router Ports"
	# Delete the network ports from the routers
	net1 = neutron.list_networks(name="flat-lan-1-net")["networks"][0]
	net2 = neutron.list_networks(name="tun0-net")["networks"][0]
	neutron.remove_interface_router(router1['id'], {"subnet_id":net1['subnets'][0]})
	neutron.remove_interface_router(router2['id'], {"subnet_id":net2['subnets'][0]})

	for port in neutron.list_ports()['ports']:
		neutron.delete_port(port['id'])

	# Delete the routers
	print "Deleting Routers"
	neutron.delete_router(router1['id'])
	neutron.delete_router(router2['id'])
	# Delete the networks
	print "Deleting Networks"
	neutron.delete_network(net1['id'])
	neutron.delete_network(net2['id'])

if __name__ == "__main__":
	main()
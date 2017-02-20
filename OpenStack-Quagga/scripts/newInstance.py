#!/usr/bin/env python

# Written by Keith Downie
#
# Does all of the initial work for setting up the OpenStack experiment

from novaclient import client
from socket import *
import os
import time
import sys

def main():
	print sys.argv[1]+": Starting Nova Client..."
	nova = client.Client(2, username=os.environ['OS_USERNAME'], api_key=os.environ['OS_PASSWORD'], tenant_id=os.environ['OS_TENANT_ID'], auth_url=os.environ['OS_AUTH_URL'])
	flavor = nova.flavors.list()[1] #m1.small

	# Determine if this is supposed to be multinic or not
	image = nova.images.list()[1] #trusty-server
	if (sys.argv[4] == "True"):
		image = nova.images.list()[0] #trusty-server-multi-nic

	# Get the network(s) that the server needs to be assigned to
	nets = get_networks(nova.networks.list(), sys.argv)
	nics = []
	for net in nets:
		nics.append({'net-id':net.id, 'v4-fixed-ip':''})

	# Start the server up
	print sys.argv[1]+": Starting Server..."
	server = nova.servers.create(sys.argv[1], image, flavor, nics=nics, security_groups=["default"], key_name="cloud")
	status = server.status

	print sys.argv[1]+": Waiting For Server to Boot..."
	while server.status == "BUILD":
		server = nova.servers.get(server.id)
		status = server.status

	# Assign a floating IP to the server
	print sys.argv[1]+": Attaching Floating IP to "+server.networks[sys.argv[2]][0]+"..."
	fip = get_floating_ip(nova.floating_ips.list(), nova)
	nova.servers.add_floating_ip(server, fip, fixed_address=server.networks[sys.argv[2]][0])

	# If it is a multinic, test to make sure that the Floating IP was assigned correctly
	if (sys.argv[4] == "True"):
		print sys.argv[1]+": Testing Floating IP..."
		time.sleep(5)
		test = test_port(fip.ip)
		if test == False:
			print sys.argv[1]+": Attached to Wrong NIC, Adjusting to "+server.networks[sys.argv[3]][0]+"..."
			nova.servers.remove_floating_ip(server, fip)
			nova.servers.add_floating_ip(server, fip, fixed_address=server.networks[sys.argv[3]][0])
		else:
			print sys.argv[1]+": Floating IP Attached Correctly..."


# Get the specified networks and return them.
def get_networks(networks, args):
	nets = []
	for net in networks:
		if (net.label == args[2] or (args[4] == "True" and net.label == args[3])):
			nets.append(net)

	return nets

# Look and see if there is an available Floating IP.
# If not, reserve a new one and return it.
def get_floating_ip(ips, nova):
	for ip in ips:
		if ip.fixed_ip == None:
			return ip

	return nova.floating_ips.create(pool="ext-net")

# Found this way to test connectivity from StackOverflow at:
# http://stackoverflow.com/questions/3125724/network-testing-connectivity-python-or-c
def test_port(ip_address):
	result = 113
	while result == 113:
		s = socket(AF_INET, SOCK_STREAM)
		s.settimeout(3)
		result = s.connect_ex((ip_address, 22))
		s.close()

	if(result == 0 or result == 111):
		return True
	else:
		return False

if __name__ == "__main__":
	main()
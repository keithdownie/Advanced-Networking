#!/usr/bin/env python

# Written by Keith Downie
#
# Used for releasing the floating IPs that the instances are using.

from novaclient import client
import os
import sys

def main():
	print sys.argv[1]+": Starting Nova Client..."
	nova = client.Client(2, username=os.environ['OS_USERNAME'], api_key=os.environ['OS_PASSWORD'], tenant_id=os.environ['OS_TENANT_ID'], auth_url=os.environ['OS_AUTH_URL'])
	print sys.argv[1]+": Releasing Floating IP..."
	# Get the specified server info
	server = nova.servers.list(search_opts={'name':sys.argv[1]})[0]
	try:
		# If there is a floating IP, remove it
		server.remove_floating_ip(find_floating_ip(server))
	except Exception:
		pass

	print sys.argv[1]+": Deleting..."
	# Delete the server
	server.delete()

def find_floating_ip(server):
	for nic, addr in server.networks.iteritems():
		if len(addr) == 2:
			return addr[1]

if __name__ == "__main__":
	main()
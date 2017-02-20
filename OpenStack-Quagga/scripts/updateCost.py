# Written by Keith Downie
#
# Script used to update the cost of a network path in OSPF.
# Used for redirecting network traffic.

from novaclient import client
import os
import sys

def main():
	print "Starting Nova Client..."
	# Get passsed in arguments
	target = sys.argv[1]
	cost = sys.argv[2]
	nova = client.Client(2, username=os.environ['OS_USERNAME'], api_key=os.environ['OS_PASSWORD'], tenant_id=os.environ['OS_TENANT_ID'], auth_url=os.environ['OS_AUTH_URL'])

	# Find the server that was specified
	server = nova.servers.list(search_opts={'name':target})[0]
	serverIP = find_floating_ip(server)
	
	print "Installing OSPF Settings on "+target
	opts = " -i cloud.key -o StrictHostKeyChecking=no"

	# Update the cost of eth0 and eth1 on the server
	os.system("ssh"+opts+" root@"+serverIP+" 'vtysh -c \"config t\" -c \"router ospf\" -c \"interface eth0\" -c \"ip ospf cost "+cost+"\"'")
	os.system("ssh"+opts+" root@"+serverIP+" 'vtysh -c \"config t\" -c \"router ospf\" -c \"interface eth1\" -c \"ip ospf cost "+cost+"\"'")

def find_floating_ip(server):
	for nic, addr in server.networks.iteritems():
		if len(addr) == 2:
			return addr[1]

if __name__ == "__main__":
	main()
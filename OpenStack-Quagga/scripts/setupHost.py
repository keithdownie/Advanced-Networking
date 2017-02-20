# Written by Keith Downie
#
# Creates and sets up a single client using Nova

from novaclient import client
import os
import sys

def main():
	print "Starting Nova Client..."
	# Get passed in arguments
	target = sys.argv[1]
	targetRouter = sys.argv[2]
	nova = client.Client(2, username=os.environ['OS_USERNAME'], api_key=os.environ['OS_PASSWORD'], tenant_id=os.environ['OS_TENANT_ID'], auth_url=os.environ['OS_AUTH_URL'])

	# Get the specified host and router
	server = nova.servers.list(search_opts={'name':target})[0]
	serverIP = find_floating_ip(server)
	router = nova.servers.list(search_opts={'name':targetRouter})[0]
	
	# Get the settings that need to be installed
	print "Installing Route Settings on "+target
	sub = None
	routeSub = None
	for nic,net in server.networks.iteritems():
		sub = str(net[0])[5:-2]
	for nic,net in router.networks.iteritems():
		if str(net[0])[5:-2] == sub:
			routeSub = str(net[0])

	opts = " -i cloud.key -o StrictHostKeyChecking=no"

	# Set up the routes on the host
	for i in range(10):
		if '1'+str(i) != sub:
			os.system("ssh"+opts+" root@"+serverIP+" route add -net 10.0.1"+str(i)+".0/24 gw "+routeSub)
	print "Checking if Traceroute is Installed"

	# Install traceroute since it will be needed
	print os.system("ssh"+opts+" root@"+serverIP+" 'sudo apt-get update'")
	print os.system("ssh"+opts+" root@"+serverIP+" 'sudo apt-get install traceroute -y'")

def find_floating_ip(server):
	for nic, addr in server.networks.iteritems():
		if len(addr) == 2:
			return addr[1]

if __name__ == "__main__":
	main()
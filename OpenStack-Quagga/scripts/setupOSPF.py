# Written by Keith Downie
#
# Creates a single Nova client for routing traffic.
# Also registers node with OSPF.

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
	# Send over the modified daemons file
	os.system("scp"+opts+" daemons root@"+serverIP+":~/")
	# Run the remote setup script to set up the conf files
	os.system("ssh"+opts+" root@"+serverIP+" 'bash -s' < remoteSetup.sh")

	# Customize the ospfd conf file based on the current server
	os.system("ssh"+opts+" root@"+serverIP+" 'echo \"!\" >> /etc/quagga/ospfd.conf'")
	os.system("ssh"+opts+" root@"+serverIP+" 'echo \"router ospf\" >> /etc/quagga/ospfd.conf'")
	for nic,net in server.networks.iteritems():
		sub = str(net[0])[:-2]
		os.system("ssh"+opts+" root@"+serverIP+" 'echo \"  network "+sub+".0/24 area 0.0.0.0\" >> /etc/quagga/ospfd.conf'")
	os.system("ssh"+opts+" root@"+serverIP+" 'echo \"!\" >> /etc/quagga/ospfd.conf'")
	os.system("ssh"+opts+" root@"+serverIP+" 'echo \"interface eth0\" >> /etc/quagga/ospfd.conf'")
	os.system("ssh"+opts+" root@"+serverIP+" 'echo \"  ip ospf cost "+cost+"\" >> /etc/quagga/ospfd.conf'")
	os.system("ssh"+opts+" root@"+serverIP+" 'echo \"!\" >> /etc/quagga/ospfd.conf'")
	os.system("ssh"+opts+" root@"+serverIP+" 'echo \"interface eth1\" >> /etc/quagga/ospfd.conf'")
	os.system("ssh"+opts+" root@"+serverIP+" 'echo \"  ip ospf cost "+cost+"\" >> /etc/quagga/ospfd.conf'")
	os.system("ssh"+opts+" root@"+serverIP+" 'echo \"!\" >> /etc/quagga/ospfd.conf'")

	# Start Quagga
	os.system("ssh"+opts+" root@"+serverIP+" '/etc/init.d/quagga start'")

def find_floating_ip(server):
	for nic, addr in server.networks.iteritems():
		if len(addr) == 2:
			return addr[1]

if __name__ == "__main__":
	main()
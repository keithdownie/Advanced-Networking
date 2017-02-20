#!/usr/bin/python

# Written by Keith Downie
#
# Mininet script to simulate three hosts communicating through
# an OpenFlow switch running a POX controller. The controller
# that runs is located in kdpox.py
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at:
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from mininet.topo import SingleSwitchTopo
from mininet.net import Mininet
from mininet.log import setLogLevel
from mininet.node import RemoteController
import time

def pingTest(N=3):
        c0 = RemoteController('c0', ip='0.0.0.0', port=6633)
	topo = SingleSwitchTopo(N)
	net = Mininet(topo, controller=c0)
	net.start()
        print 'Set bridge s1 to OpenFlow10'
        net.switches[0].cmd('ovs-vsctl set bridge s1 protocols=OpenFlow10')
	hosts = net.hosts

	print 'Starting pings'
	hosts[0].cmdPrint('ping', '-c 10', "h3")
        hosts[1].cmdPrint('ping', '-c 10', "h3")
        
	net.stop()

if __name__ == '__main__':
	setLogLevel('info')
        pingTest()

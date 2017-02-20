# Written by Keith Downie
#
# Controller's goal is to hide the true IP address of a designated
# "protected" host. To achieve this, there are three areas of networking
# that are used: ARP, DNS, and IP. 
#
# The controller monitors these three types of requests for packets that
# are trying to locate or communicate with the protected host. When it 
# finds such a packet, it hides the true IP of the host by modifying
# and retransmitting packets with a "fake" address for the host.
#
# Communication between hosts that are not protected is not modified
# and passes through the controller without modification.
#
# For ARP functionality, borrowed from POX examples written by James McCauley
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

from pox.core import core
import pox
import time
log = core.getLogger()

from pox.lib.packet.ethernet import ethernet, ETHER_BROADCAST
from pox.lib.addresses import IPAddr, EthAddr
from pox.lib.packet.ipv4 import ipv4
from pox.lib.packet.arp import arp
from pox.lib.packet.udp import udp
from pox.lib.packet.dns import dns
from pox.lib.recoco import Timer

import pox.openflow.libopenflow_01 as of

from pox.lib.revent import *

# Entry class from ~/pox/pox/forwarding/l3_learning.py
class Entry (object):
  def __init__ (self, port, mac):
    self.timeout = time.time() + 120
    self.port = port
    self.mac = mac

  def __eq__ (self, other):
    if type(other) == tuple:
      return (self.port,self.mac)==other
    else:
      return (self.port,self.mac)==(other.port,other.mac)
  def __ne__ (self, other):
    return not self.__eq__(other)

  def isExpired (self):
    if self.port == of.OFPP_NONE: return False
    return time.time() > self.timeout


def dpid_to_mac (dpid):
  return EthAddr("%012x" % (dpid & 0xffFFffFFffFF,))


class pox_controller (EventMixin):
  def __init__ (self):
    
    self.outstanding_arps = {}

    # (dpid,IP) -> [(expire_time,buffer_id,in_port), ...]
    # These are buffers we've gotten at this datapath for this IP which
    # we can't deliver because we don't know where they go.
    self.buffer = {}

    # For each switch, we map IP addresses to Entries
    self.arpTable = {}

    # This timer handles expiring stuff
    self._expire_timer = Timer(5, self._handle_expiration, recurring=True)

    # IP address to protect
    self.trueIP = IPAddr('10.0.0.3')
    self.ipMapping = {}
    self.ipOffset = 11;

    core.listen_to_dependencies(self)
# _handle_expiration function from ~/pox/pox/forwarding/l3_learning.py
  def _handle_expiration (self):
    # Called by a timer so that we can remove old items.
    empty = []
    for k,v in self.buffer.iteritems():
      dpid,ip = k

      for item in list(v):
        expires_at,buffer_id,in_port = item
        if expires_at < time.time():
          # This packet is old.  Tell this switch to drop it.
          v.remove(item)
          po = of.ofp_packet_out(buffer_id = buffer_id, in_port = in_port)
          core.openflow.sendToDPID(dpid, po)
      if len(v) == 0: empty.append(k)

    # Remove empty buffer bins
    for k in empty:
      del self.buffer[k]

  def _send_buffer (self, dpid, ipaddr, macaddr, port):
    if (dpid,ipaddr) in self.buffer:
      bucket = self.buffer[(dpid,ipaddr)]
      del self.buffer[(dpid,ipaddr)]

      for _,buffer_id,in_port in bucket:
        po = of.ofp_packet_out(buffer_id=buffer_id,in_port=in_port)
        po.actions.append(of.ofp_action_dl_addr.set_dst(macaddr))
        po.actions.append(of.ofp_action_output(port = port))
        core.openflow.sendToDPID(dpid, po)

  def _handle_openflow_PacketIn (self, event):
    dpid = event.connection.dpid
    inport = event.port
    packet = event.parsed

    if dpid not in self.arpTable:
      # We've come across a new switch
      self.arpTable[dpid] = {}
      # Add the 10.0.0.10 false address in order to pick up on DNS traffic
      self.arpTable[dpid][IPAddr('10.0.0.10')] = Entry(of.OFPP_NONE, dpid_to_mac(dpid))

    # The two types of packets we care about are IPv4 and ARP packets, so that's all we will check for.
    if isinstance(packet.next, ipv4):
        # Check and see if the IPv4 packet is a DNS packet or not
        if packet.next.find('dns'):
            pac = packet.next.find('dns')
            # Loop through each of the questions, though in this assignment there should only be one
            for question in pac.questions:
              # If they are looking for the protected host, in this case h3, then resolve the DNS
              if question.name[:2] == 'h3':
                log.debug(" Received DNS request for %s", question.name)
                # Make a new IP address. Simple algorithm, starts at 10.0.0.11 and goes up from there each time.
                newIP = IPAddr('10.0.0.'+str(self.ipOffset))
                self.ipOffset += 1
                log.debug(" Sent bogus IP Address %s to %s", newIP, packet.next.srcip)
                self.ipMapping[packet.next.srcip] = newIP

                # Set up the reply DNS packet and send it out
                pac.answers.append(pac.rr(question.name, question.qtype, question.qclass, 100, str(len(newIP)), newIP))
                pac.qr = True
                pac.ra = True
                udpp = udp()
                udpp.dstport = packet.next.find('udp').srcport
                udpp.srcport = packet.next.find('udp').dstport
                udpp.payload = pac

                ipp = ipv4()
                ipp.protocol = ipp.UDP_PROTOCOL
                ipp.srcip = packet.next.dstip
                ipp.dstip = packet.next.srcip
                ipp.payload = udpp

                e = ethernet(type=ethernet.IP_TYPE, src=packet.dst, dst=packet.src)
                e.payload = ipp
                msg = of.ofp_packet_out()
                msg.data = e.pack()
                msg.actions.append(of.ofp_action_output(port = of.OFPP_IN_PORT))
                msg.in_port = inport
                event.connection.send(msg)
        else:
            # Just a normal IPv4 packet
            log.debug("%i %i IP %s => %s", dpid,inport,
                      packet.next.srcip,packet.next.dstip)
            storesrc = packet.next.srcip
            if packet.next.srcip in self.ipMapping:
              packet.next.dstip = self.trueIP
              log.debug(" Translated %s to %s", self.ipMapping[packet.next.srcip], self.trueIP)
            elif packet.next.dstip in self.ipMapping:
              log.debug(" Translated %s to %s", self.trueIP, self.ipMapping[packet.next.dstip])
              packet.next.srcip = self.ipMapping[packet.next.dstip]

            # Empty out the buffer of pending packets
            self._send_buffer(dpid, packet.next.srcip, packet.src, inport)

            # If we haven't seen the source IP before, add it to the ARP table
            if packet.next.srcip not in self.arpTable[dpid]:
                log.debug("%i %i learned %s", dpid,inport,packet.next.srcip)
            self.arpTable[dpid][packet.next.srcip] = Entry(inport, packet.src)

            # Rather than using flows, since each packet needs to have the protected IP modified
            # we need to see every packet. This forwards the packet with the modified IP address.
            if packet.next.dstip in self.arpTable[dpid]:
              packet.dst = self.arpTable[dpid][packet.next.dstip].mac
              msg = of.ofp_packet_out()
              msg.actions.append(of.ofp_action_output(port = self.arpTable[dpid][packet.next.dstip].port))
              msg.data = packet.pack()
              msg.in_port = event.port
              event.connection.send(msg)

    elif isinstance(packet.next, arp):
      # Got an ARP packet
      ap = packet.next
    
      which = {arp.REQUEST:1,arp.REPLY:0}.get(ap.opcode,
       'op:%i' % (ap.opcode,))
      # Save the old values to have the correct mappings to internal structures.
      storesrc = ap.protosrc
      storedst = ap.protodst
      # See if this is a request or a reply ARP in order to swap the right IP address.
      if ap.opcode == arp.REQUEST:
        if ap.protosrc in self.ipMapping:
          log.debug(" Translated %s to %s", self.ipMapping[ap.protosrc], self.trueIP)
          ap.protodst = self.trueIP
      elif ap.protosrc == self.trueIP:
        if ap.protodst in self.ipMapping:
          ap.protosrc = self.ipMapping[ap.protodst]

      log.debug("%i %i ARP %s %s => %s", dpid, inport,
       {arp.REQUEST:"request",arp.REPLY:"reply"}.get(ap.opcode,
       'op:%i' % (ap.opcode,)), ap.protosrc, ap.protodst)

      if ap.prototype == arp.PROTO_TYPE_IP:
        if ap.hwtype == arp.HW_TYPE_ETHERNET:
          if ap.protosrc != 0:
            # If the source is new to us, add it to the ARP table
            if storesrc not in self.arpTable[dpid]:
              log.debug("%i %i learned %s", dpid,inport,storesrc)
            self.arpTable[dpid][storesrc] = Entry(inport, packet.src)

            # Send any waiting packets
            self._send_buffer(dpid, ap.protosrc, packet.src, inport)

            if ap.opcode == arp.REQUEST:
              if ap.protodst in self.arpTable[dpid]:
                # There is a matching entry in the ARP table
                if not self.arpTable[dpid][ap.protodst].isExpired():
                  # .. and it's relatively current, so we'll reply ourselves

                  r = arp()
                  r.hwtype = ap.hwtype
                  r.prototype = ap.prototype
                  r.hwlen = ap.hwlen
                  r.protolen = ap.protolen
                  r.opcode = arp.REPLY
                  r.hwdst = ap.hwsrc
                  r.protodst = ap.protosrc
                  r.protosrc = storedst
                  r.hwsrc = self.arpTable[dpid][ap.protodst].mac
                  e = ethernet(type=packet.type, src=dpid_to_mac(dpid),
                               dst=ap.hwsrc)
                  e.set_payload(r)
                  log.debug("%i %i answering ARP for %s" % (dpid, inport,
                   r.protosrc))
                  msg = of.ofp_packet_out()
                  msg.data = e.pack()
                  msg.actions.append(of.ofp_action_output(port =
                                                          of.OFPP_IN_PORT))
                  msg.in_port = inport
                  event.connection.send(msg)
                  return

      # To prevent the hosts from knowing the protected IP, retransmit all ARPs from the controller
      if (dpid,ap.protodst) not in self.buffer:
        self.buffer[(dpid,ap.protodst)] = []
        bucket = self.buffer[(dpid,ap.protodst)]
        entry = (time.time() + 5,event.ofp.buffer_id,inport)
        bucket.append(entry)
        while len(bucket) > 5: del bucket[0]

        # Expire things from our outstanding ARP list
        self.outstanding_arps = {k:v for k,v in
                                 self.outstanding_arps.iteritems() if v > time.time()}

        # Check if we've already ARPed recently to prevent spamming
        if (dpid,ap.protodst) in self.outstanding_arps:
          return
        self.outstanding_arps[(dpid,ap.protodst)] = time.time() + 4

        # Send out the ARP
        r = arp()
        r.hwtype = r.HW_TYPE_ETHERNET
        r.prototype = r.PROTO_TYPE_IP
        r.hwlen = 6
        r.protolen = r.protolen
        r.opcode = r.REQUEST
        r.hwdst = ETHER_BROADCAST
        r.protodst = ap.protodst
        r.hwsrc = packet.src
        r.protosrc = storesrc
        e = ethernet(type=ethernet.ARP_TYPE, src=packet.src,
                     dst=ETHER_BROADCAST)
        e.set_payload(r)
        log.debug("%i %i ARPing for %s on behalf of %s" % (dpid, inport,
                                                           r.protodst, r.protosrc))
        msg = of.ofp_packet_out()
        msg.data = e.pack()
        msg.actions.append(of.ofp_action_output(port = of.OFPP_FLOOD))
        msg.in_port = inport
        event.connection.send(msg)

      

def launch ():
  core.registerNew(pox_controller)
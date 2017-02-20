Project work for CS 6480: Advanced Networking. This repo contains two of the larger projects from this class, which are detailed below.

OpenFlow-POX

This project was to experiment with Software Defined Networking (SDN). Specifically, using an OpenFlow switch that is running a POX controller. The goal of the POX controller was to create a system where the IP address of a "protected" host could be hidden from the outside world by manipulating and retransmitting incoming ARP, DNS, and IP packets related to that protected host.

OpenStack-Quagga

This project was related to a section of class dedicated to studying various types of Network Function Virtualization (NFV), as well as learn more about networking and scalability in Cloud Computing environments. 

The situation that we were addressing is as follows: There are two hosts that are communicating. Along the network path between these two hosts are three nodes, R1, R2, and R3. During this communication, R2 needs to be brought down for unexpected maintenance. The goal of the project was to create a NFV that would bring up an additional node, R4, replicate the network path of R2, and then redirect network traffic away from R2. This was all to be done without losing any packets.

For traffic routing, OSPF through Quagga was used to set and modify the flow of traffic through the cloud network. For modifying the cloud and network topology, the OpenStack API is used to create and modify nodes, hosts, and subnets.
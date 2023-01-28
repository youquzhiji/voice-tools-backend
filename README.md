# Voice Tools Backend
 
Using community-based distributed computing of untrusted nodes to accelerate ML computation, inspired by Folding@Home.

## Introduction

Existing distributed computing solutions using the map-reduce technique such as Hadoop requires a cluster of trusted nodes connected with high-speed local-area internet. However, without enough funding, creating an expensive cluster to scale up the computation wouldn't be viable.

However, a useful project can have a very large community. Even though very few people in the community are willing to donate funds to the project, many of them have capable computers that are resting most of the time. We predict that a lot more people are willing to contribute by donating their resting computational resources since a donation like this will have minimal cost to them.

This project aims to create a distributed cluster utilizing resting computational resources of willing contributors in the community. Our final goal is to create a program that anyone can run on their personal computers to turn their computer into a node in the cluster.

## Problems & Solutions

### 1. Public IP Address Availability Issue

In a commercial cluster with servers connected via a local-area network with industry-level network cards and switches, every node has an IP address with full port access that can be used to receive commands. However, not every home network has public IP addresses, which is especially true in crowdy countries like China, where it is extremely rare to have an IP address that's not shared by their entire apartment building. Also, we cannot assume that our community members have the technical knowledge to forward their ports in their routers even if they have a public IP address.

We solved this concern by using WebSocket, where the home computers send WebSocket connection request to the coordinator server on initialization, which enables the coordinator to send commands back as long as the connection is active. This method only requires the coordinator server to have a public IP address, and not the home computer. For enhanced security, we used end-to-end encryption enabled by WSS (WebSocket Secure), which handles low-level requests over HTTPS rather than HTTP.

### 2. Trust Issue

Even though we would like to believe that everyone in the world are good and will run an unmodified version of our code, this is often not true in reality. Many people might be motivated to break our services, such as transphobic people or ransom-demanding hackers. Therefore, we need a way to ensure the authenticity of the endpoint code.

However, this is not an easy task as there isn't a way to prevent modification of the code. Online-multiplayer game developers have been trying to solve this problem forever in a cat-and-mouse game with cheats and anti-cheats. They have came up with cleaver tricks such as building modification or hooking detection in kernel-level drivers, but it won't take long before it is cracked again.

Therefore, we gave up on preventing modification on the code level, but since the output of our code on the same input should be the same, we used output verification to ensure authenticity. For each home computer, the coordinator will assign a "trusted level" variable--a ratio indicating how much we trust this computer. First, we will manually assign our own servers as fully trusted (`trusted_level = 1.0`). Then, for the nodes we cannot fully trust, the coordinator will randomly select user requests to verify compared to a trusted server, with a probability based on the trusted level. If the results do not match, the coordinator will ban the target computer. Since endpoints cannot know which requests are being verified, they cannot provide fraudulent results on a massive scale without being banned.

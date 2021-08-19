#!/usr/bin/env python
# coding: utf-8

import os
import time


def partitionChanger(partitions):
    
    # stop neo4j as we delete topics to which consumers are subscribed
    commands = ["sudo systemctl stop neo4j",
                "kafka-topics --zookeeper localhost:2181 --delete --topic blocks",
                "kafka-topics --zookeeper localhost:2181 --delete --topic transactions",
                f"kafka-topics --create  --zookeeper localhost:2181 --topic blocks --replication-factor 1 --partitions {partitions}",
                f"kafka-topics --create  --zookeeper localhost:2181 --topic transactions --replication-factor 1 --partitions {partitions}",
                "sudo systemctl start neo4j"]
    for i in commands:
        stream = os.popen(i)
        time.sleep(10)
    
    # allow time until neo4j is active again 
    time.sleep(30)
        
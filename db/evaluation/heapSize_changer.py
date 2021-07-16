#!/usr/bin/env python
# coding: utf-8

import os

def heapSizeChanger(heapSize):
    commands = [ "sudo systemctl stop neo4j", "cd /etc/neo4j/", 
                 f"sed -i '/dbms.memory.heap.initial_size/c\dbms.memory.heap.initial_size={heapSize}g' neo4j.conf",
                 f"sed -i '/dbms.memory.heap.max_size/c\dbms.memory.heap.max_size={heapSize}g' neo4j.conf",
                "sudo systemctl start neo4j"]
    for i in commands:
        stream = os.popen(i)
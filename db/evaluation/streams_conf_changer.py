#!/usr/bin/env python
# coding: utf-8

# # Changing Streams.conf

from cypher_queries import *


# change cypher template in streams file 
def changeStreamsFile(path, kafka_topics, evaluate_original, matchOnAddress, getTemplate, node_labels, evaluation):


    cyphertemplate_identifier = 'streams.sink.topic.cypher'
    
    # read stream.conf
    file  = open(path, 'r')
    lines = file.readlines()
    
    for i in range(len(lines)):

        for topic in kafka_topics.keys():
            
            identifier = cyphertemplate_identifier + '.' + kafka_topics[topic]
            if lines[i].startswith(identifier):
                
                                    #topic, evaluate_original, matchOnAddress, getTemplate, node_labels):
                lines[i] = identifier + ' =' + getCypherQueries(kafka_topics[topic], 
                                                                evaluate_original, 
                                                                matchOnAddress, 
                                                                getTemplate, 
                                                                node_labels, 
                                                                evaluation) + '\n'                
                print(lines[i])

                
    # write file back 
    file = open(path, 'w')
    file.writelines(lines)
    file.close()
                

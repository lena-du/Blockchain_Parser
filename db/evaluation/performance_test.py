#!/usr/bin/env python
# coding: utf-8

# In[ ]:


#!/usr/bin/env python
# coding: utf-8

# import packages
import os
import sys
import time
sys.path.append("../")
from neo4jConnector import startNeo4jSession
from bitcoin_rpc import *
from kafka_producer import * 




# functions
# get the last transaction of the last block inserted
def getTxidQuery(session, transactionLabel, txid):
    query=f"""MATCH (n:{transactionLabel})
    WHERE n.txid="{txid}"
    RETURN n""" 
    return query

# get the creation time of a block
def getCreationTimeBlock(session, blockLabel):
    query=f"""MATCH (n:{blockLabel}) 
    RETURN n.creationTime 
    ORDER BY n.creationTime ASC"""
    result = session.run(query).values()
    creationTime=result[0][0]/1000
    return creationTime

def runPerformanceTest(evaluate_original, 
                       node_labels, 
                       bypass_kafka, 
                       start_block_height, 
                       end_block_height, 
                       match_on_previous_add, 
                       kafka_topics):

    startBlock = start_block_height
    endBlock   = end_block_height
    driver, session = startNeo4jSession() 
    
    if evaluate_original == True:
        blockLabel       = node_labels['original']['block']
        transactionLabel = node_labels['original']['transaction']
        
    else:
        blockLabel       = node_labels['test']['block']
        transactionLabel = node_labels['test']['transaction']

        
    # retrieval of the last txid for the last block inserted
    blockhash=getBlockHash(endBlock-1)
    data, block = getblock(blockhash)
    txid = block['tx'][-1]['txid']
    
    # assinging -1 as indicator that the measurement did not proceed as intended
    endTimePart1       = -1
    endTimePart2       = -1
    totalExecutionTime = -1

    # start timer 
    startTime=time.time()

    if bypass_kafka == False:
        kafkaProducer(startBlock       = start_block_height, 
                      endBlock         = end_block_height, 
                      getInput         = match_on_previous_add,
                      blockTopic       = kafka_topics['block'], 
                      transactionTopic = kafka_topics['transaction'])
    else:
        directNeoImport(startBlock       = start_block_height,
                        getInput         = False,
                        endBlock         = end_block_height)


    finishPart1 = time.time()
    endTimePart1 = finishPart1 - startTime


    # query neo4j iteratively for the last transaction & parametrize - 1 block ~ max 10 min insertion time 
    secondsToSleep = 5 
    totalBlocks=endBlock-startBlock
    timeOutReached=True
    
    for i in range(totalBlocks*10*60):
        queryresult = session.run(getTxidQuery(session, transactionLabel, txid)).values()
        if queryresult == []:
            # sleep for some seconds
            time.sleep(secondsToSleep)
        else: 
            lastNodeTime=time.time()
            timeOutReached=False
            break
            
    # approach : exit the endless loop (!)    
    if timeOutReached==True:
        print("Timeout : Blocks failed to get inserted within the predefined time limit")
    else: 
        #get times of the nodes inserted + calculate/print endTimes
        timeBlock=getCreationTimeBlock(session, blockLabel)
        endTimePart2=lastNodeTime - timeBlock
        
    totalExecutionTime = lastNodeTime - startTime
    
    return endTimePart1, endTimePart2, totalExecutionTime, timeOutReached






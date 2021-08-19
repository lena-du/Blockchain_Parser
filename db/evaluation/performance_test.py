#!/usr/bin/env python
# coding: utf-8

# import packages
import os
import sys
import time
from directNeo4jImporter import *
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

# get creationTime property of the first block inserted
def getCreationTimeBlock(session, blockLabel, start_block_height):
    query=f"""MATCH (n:{blockLabel} {{height: {start_block_height}}}) 
    RETURN n.creationTime"""
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
    
    # define neo4j node labels accordingly
    if evaluate_original == True:
        blockLabel       = node_labels['original']['block']
        transactionLabel = node_labels['original']['transaction']
        
    else:
        blockLabel       = node_labels['test']['block']
        transactionLabel = node_labels['test']['transaction']

        
    # retrieval of the last txid for the last block inserted
    blockhash=getBlockHash(endBlock-1)
    key, data, block = getBlock(blockhash)
    txid = block['tx'][-1]['txid']
    
    # assinging -1 as indicator that the measurement did not proceed as intended
    endTimePart1       = -1
    endTimePart2       = -1
    totalExecutionTime = -1
    
    
    # prepare queries and functions to insert for bypassing kafka
    if bypass_kafka == True: 
        queryBlocks = getCypherQueries(topic = kafka_topics['block'], 
                                   matchOnAddress = False, 
                                   evaluation = True,
                                   getTemplate = False, 
                                   node_labels = node_labels,
                                   evaluate_original = evaluate_original)

        queryTransactions = getCypherQueries(topic = kafka_topics['transaction'], 
                                   matchOnAddress = False, 
                                   evaluation = True,
                                   getTemplate = False, 
                                   node_labels = node_labels,
                                   evaluate_original = evaluate_original)

        def run_tx(tx, event):
            tx.run(queryTransactions, 
                   txid         = event["txid"], 
                   output_list  = event["output_list"], 
                   block_hash   = event["block_hash"], 
                   inDegree     = event["inDegree"], 
                   outDegree    = event["outDegree"], 
                   outSum       = event["outSum"],
                   inSum        = event["inSum"],
                   input_list   = event["input_list"], 
                   block_date   = event["block_date"])

        def create_block(tx, event):
            tx.run(queryBlocks, 
                   block_hash        = event['block_hash'], 
                   block_height      = event['block_height'], 
                   block_median_time = event['block_median_time'], 
                   block_date        = event['block_date'],
                   previousblockhash = event['previousblockhash'])
    
            
    # start timer 
    startTime=time.time()
    
    # call kafka producer or bypassing script for insertion
    if bypass_kafka == False: 
        for blockHeight in range(startBlock, endBlock):
         
            kafkaProducer(blockHeight      = blockHeight,
                              getInput         = match_on_previous_add,
                              blockTopic       = kafka_topics['block'], 
                              transactionTopic = kafka_topics['transaction'], 
                              importBlock      = True, 
                              txOffset         = 0)

            
    else:
        
        directNeoImport(startBlock        = start_block_height,
                        endBlock          = end_block_height, 
                        kafka_topics      = kafka_topics, 
                        node_labels       = node_labels, 
                        evaluate_original = evaluate_original, 
                        run_tx            = run_tx, 
                        create_block      = create_block,
                        queryBlocks       = queryBlocks,
                        queryTransactions = queryTransactions,
                        driver            = driver,
                        session           = session)
       
    # part 1 of the pipeline -finished
    finishPart1 = time.time()
    endTimePart1 = finishPart1 - startTime


    # query neo4j iteratively for the last transaction 
    # parametrize querying attempts -> processing of a block within 10 min 
    secondsToSleep = 1
    totalBlocks=endBlock-startBlock
    timeOutReached=True
    
    for i in range(totalBlocks*10*60):
        queryresult = session.run(getTxidQuery(session, transactionLabel, txid)).values()
        if queryresult == []:
            # sleep for some seconds
            time.sleep(secondsToSleep)
        else:
            # last transaction found
            lastNodeTime=time.time()
            timeOutReached=False
            break
            
    # exit in case of endless loop    
    if timeOutReached==True:
        print("Timeout : Blocks failed to get inserted within the predefined time limit")
    else: 
        # get creationTime of block 
        timeBlock=getCreationTimeBlock(session, blockLabel, start_block_height)
        # part 2 of the pipeline finished
        endTimePart2=lastNodeTime - timeBlock
        
    totalExecutionTime = lastNodeTime - startTime
    
    session.close()
    driver.close()
    
    return endTimePart1, endTimePart2, totalExecutionTime, timeOutReached
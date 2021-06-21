#!/usr/bin/env python
# coding: utf-8

# In[ ]:


#!/usr/bin/env python
# coding: utf-8

# import packages
import os
import sys
import time
import datetime as dt
from bitcoin_rpc import *
from kafka import KafkaProducer
from neo4jConnector import startNeo4jSession

# establish Kafka producer
producer = KafkaProducer(bootstrap_servers='localhost:9092')
producer = KafkaProducer(value_serializer=lambda v: json.dumps(v).encode('utf-8'))


# In[ ]:


# handover command line arguments
startBlock = int(sys.argv[1])
endBlock   = int(sys.argv[2])
block_topic = sys.argv[3]
transaction_topic = sys.argv[4]
deleteAll = sys.argv[5]


startTime=time.time()

for blockheight in range(startBlock,endBlock):
    try:
      # retrival of block + transfer to the respective topic
      blockhash = getBlockHash(blockheight)
      data, block = getblock(blockhash)
      producer.send(block_topic, data)
    except:
      print('Error handling block at height' + str(blockheight) + 'with blockhash' + str(blockhash))


    # retrival of transactions + transfer to the respective topic
    for txid in block['tx'][:]:
        try:
            tx = gettx(txid,block)
            producer.send(transaction_topic, tx)
        except:
            print('Error handling transactions at block' + str(blockheight) + ' with transaction id' + str(txid['txid']))

finishPart1 = time.time()
endTimePart1 = finishPart1 - startTime


# In[ ]:


driver, session = startNeo4jSession() 

# retrieval of the last txid for the last block inserted

blockhash=getBlockHash(endBlock-1)
data, block = getblock(blockhash)
txid = block['tx'][-1]['txid']

def getTxidQuery(txid):
    query=f"""MATCH (n:Transaction_test)
    WHERE n.txid="{txid}"
    RETURN n""" 
    return query

# query neo4j iteratively to check if the last transaction node has been added 


secondsToSleep = 5  

for i in range(200):
    queryresult =session.run(getTxidQuery(txid)).values()
    if queryresult == []:
        # sleep for some seconds
        time.sleep(secondsToSleep)
    else: 
        lastNodeTimeQuery=time.time()
        break
        

# get the creation time of a particular node
def getCreationTime(node):
    nodeType=node
    if nodeType=="Block_test":
        orderParameter="ASC"
    else:
        orderParameter="DESC"
    query=f"""MATCH (n:{nodeType}) 
    RETURN n.creationTime 
    ORDER BY n.creationTime {orderParameter}"""
    result = session.run(query).values()
    creationTime=result[0][0]/1000
    return creationTime

timeBlock=getCreationTime("Block_test")
timeTransaction=getCreationTime("Transaction_test")
timeAddress=getCreationTime("Address_test")

lastNodeTime=max(timeTransaction, timeAddress)

# endTimePart2=lastNodeTime-timeBlock

endTimePart2Query=lastNodeTimeQuery - timeBlock
neo4jTimeLag=lastNodeTimeQuery - lastNodeTime


# In[ ]:


endTime=lastNodeTimeQuery-startTime

# nr of blocks inserted
totalBlocks=endBlock-startBlock

print('Execution time for the first part of the pipeline BTC-Kafka is ' + str(endTimePart1) + ' sec')
print('Execution time for the second part of the pipeline Kafka-Neo4j is ' + str(endTimePart2Query) + ' sec')
print('Total execution time for the retrieval and insertion of ' + str(totalBlocks) + ' blocks is ' + str(endTime) + ' sec')
print('Neo4j time lag for the creation and insertion of the last node is ' + str(neo4jTimeLag) + ' sec')

print('--------------------------------------------Time Conversions')
part1 = dt.datetime.fromtimestamp(finishPart1)
blockCreated=dt.datetime.fromtimestamp(timeBlock)
transactionCreated=dt.datetime.fromtimestamp(timeTransaction)
addressCreated=dt.datetime.fromtimestamp(timeAddress)
lastNodeQueried=dt.datetime.fromtimestamp(lastNodeTimeQuery)

print('Part 1 of the pipeline finishes at ' + str(part1))
print('1st block node creationTime ' + str(blockCreated))
print('Last transaction node creationTime ' + str(transactionCreated))
print('Last address node creationTime ' + str(addressCreated))
print('Last transaction node inserted queriedTime ' + str(lastNodeQueried))


queries = ["MATCH (n:Block_test) DETACH DELETE n", "MATCH (n:Transaction_test) DETACH DELETE n", "MATCH (n:Address_test) DETACH DELETE n"]

if deleteAll == 'yes':
    for query in queries:
        session.run(query)


driver.close()
session.close()


# Maybe additionally modify print output : seconds to minutes


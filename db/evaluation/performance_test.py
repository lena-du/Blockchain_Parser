#!/usr/bin/env python
# coding: utf-8

# # Performance Test


#import packages
import os
import sys
from bitcoin_rpc import * 
from neo4jConnector import startNeo4jSession


#hand over arguments
try:
    start_block = int(sys.argv[1])
    end_block   = int(sys.argv[2])
    deleteAfterwards = bool(sys.argv[3])

except:
    #set blockheight here
    start_block = 1
    end_block   = 2
    deleteAfterwards = False
    print(f'No parameters were handed over. \nUsing default parameter: Start_block {start_block}; End_block: {end_block}')

    
    
# Neo4j connection 
driver, session = startNeo4jSession()    
    
    
### Query for last block & retrieve last txid-hash
blockhash = getBlockHash(end_block - 1)
data, block = getblock(blockhash)
# last transaction
txid = block['tx'][-1]['txid']
txClass = 'Transaction_test'

def getTransactionPropertiesByTxidQuery(txClass, txid):
    return f'MATCH (t:{txClass} {{txid: \"{txid}\"}}) RETURN t'
def runQuery(query):
    return session.run(query).data()


# start timing
startTime = time.time()

# Maybe convert pipeline_testing also into a function
os.system(f'python3 pipelineP1_testing.py {start_block} {end_block}')

# iteratively query for neo4j directly, whether it returns a result for the hash of the last transaction of hte last block
# if yes, stop timing


timeOutReached = True
timeOutLimit   = 6
secondsToSleep = 5  
for i in range(timeOutLimit):
    queryresult = runQuery(getTransactionPropertiesByTxidQuery(txClass, txid))
    if queryresult == []:
        # sleep for some seconds
        time.sleep(secondsToSleep)
    else: 
        timeOutReached = False
        break

if timeOutReached == True:
    print('Time out')
    
endTime = (time.time() - startTime)
print('Retrieval and ingestion execution time in seconds: ' + str(endTime))

delete_queries = ['match (t:Block_test) detach delete t',
'match (t:Address_test) detach delete t',
'match (t:Transaction_test) detach delete t']

if deleteAfterwards == True:
    for query in delete_queries:
        session.run(query)
    
session.close()
driver.close()



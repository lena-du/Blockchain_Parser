#!/usr/bin/env python
# coding: utf-8

# ##########################
# # BITCOIN-SYNC 
# ## MAIN SCRIPT
# ##########################

##########################################
#!set absolute path to settings file here!
##########################################
 # '/home/btc/db/settings.json
settings_path = '/home/btc/db'

##########################################

import os
import json
import time
from neo4jConnector import *
from bitcoin_rpc import *
from kafka_producer import *

# read in settings

with open(settings_path+'/settings.json') as json_file:
    settings = json.load(json_file)

# parameter assignment

block_label       = settings['node_labels_neo4j']['block']
transaction_label = settings['node_labels_neo4j']['transaction']

block_topic       = settings['kafka_topics']['block']
transaction_topic = settings['kafka_topics']['transaction']




# function to retrieve latest block in Bitcoin blockchain
def getLatestBlockHeight(): 
    bestblockhash = getBestBlockHash()

    key, data, block = getBlock(bestblockhash)
    latestBlock = data['block_height']
    
    return latestBlock


### Preliminary Check


# check whether both Neo4j and Kafka are active
active = False

while active == False:
    
    # check status of kafka
    stream = os.popen('systemctl status kafka | grep Active')
    output = stream.read().strip()
    kafka_status = output.split(' ')[1]
    
    
    # check status of neo4j
    stream = os.popen('systemctl status neo4j | grep Active')
    output = stream.read().strip()
    neo4j_status = output.split(' ')[1]
    
    
    if kafka_status != 'active' or neo4j_status != 'active': 
        print("exit program")
        time.sleep(300) 
    else:
        print('Kafka: ' + kafka_status + '\nNeo4j: ' + neo4j_status)
        active = True
    

# start bitcoind 
stream = os.popen('bitcoind --daemon') 
time.sleep(6)
stream = os.popen('bitcoin-cli getblockchaininfo')
result = stream.read()

started = False
while started == False :
    try:
        blockchaininfo=json.loads(result)
        started = True
    except:
        time.sleep(10)
        stream = os.popen('bitcoin-cli getblockchaininfo')
        result = stream.read()
        
print('Bitcoind: active')


# check whether there are any messages inside the topics 
offsetZero = False

stream = os.popen('kafka-consumer-groups --describe --group neo4j --bootstrap-server localhost:9092')
output = stream.read().strip().split('\n')

for i in range(len(output)):
    output[i] = output[i].split()

output.pop(0)

countOffset=0
for i in range(len(output)):
    if output[i][1] == block_topic or output[i][1] == transaction_topic:
        offset_value = int(output[i][4])
        countOffset = countOffset + offset_value

driver, session = startNeo4jSession(
    credentials  = './credentialsNeo4j.json',
    location = 'server',
    port = 7687,
    settings_path = settings_path )

print("Start")
if countOffset == 0:
    print("STart Scenario 2.1")
    # no messages inside topics - check whether all transactions belonging to latest block in Neo4j have been inserted
    
    # get latest block in Neo4j
    query = f"""MATCH (b:{block_label}) WHERE EXISTS(b.height) RETURN b.hash ORDER BY b.height DESC LIMIT 1"""
    result = session.run(query)
    currentHash = result.values()[0][0]
    
    # RPC call for the latest block in Neo4j to retrieve list of transactions
    key, data, block = getBlock(currentHash)
    txPosition = 0
    
    for i in range(0, len(block['tx'])): 
        tx = block['tx'][i]
        txid = tx['txid']
        
        # query iteratively for the transactions in neo4j
        query = f"""MATCH (t:{transaction_label}) WHERE t.txid = '{txid}' RETURN t"""
        result = session.run(query).values()
        if result == []:
            txPosition = i
            break
        
    
    nTx = block['nTx']
    blockHeight = block['height']
    
    # check if all the transactions are inserted into Neo4j. If not, insert the remaining ones
    if txPosition != nTx:
        kafkaProducer(blockHeight, block_topic, transaction_topic, True, False, txPosition)
        print("STart Scenario 2.2")
    
    print("Finish if and Scenrai2 ")

    
else:
    # topics partitions have offsets !=0
    print("Start 3 ")
    noLag = False
    
    # wait until all kafka messages have been consumed
    while noLag == False:

        stream = os.popen('kafka-consumer-groups --describe --group neo4j --bootstrap-server localhost:9092')
        output = stream.read().strip().split('\n')

        for i in range(len(output)):
            output[i] = output[i].split()

        output.pop(0)

        lag_sum=0
        for i in range(len(output)):
            if output[i][1] == block_topic or output[i][1] == transaction_topic:
                lag_value = int(output[i][5])
                lag_sum = lag_sum + lag_value

        print(lag_sum)
        if lag_sum == 0:
            noLag = True
        else:
            time.sleep(300) 
        
        # check block offset 
        stream = os.popen(f"kafka-run-class kafka.tools.GetOffsetShell --broker-list localhost:9092 --time -1 --topic {block_topic}")
        output = stream.read().strip().split('\n')
     

        for i in range(len(output)):
            output[i] = output[i].split(':')

        keyValues = []

        for i in range(len(output)):
            partition = int(output[i][1])
            if int(output[i][2]) != 0:
                offset = int(output[i][2]) - 1
                stream = os.popen(f"kafka-console-consumer --bootstrap-server localhost:9092  --topic {block_topic}                                       --partition {partition} --offset {offset}   --property print.key=true --max-messages 1")
                outputs = stream.read().strip().split('\t')
                keyValue = int(outputs[0])
                keyValues.append(keyValue)
                

        # max heightblock inserted into kafka
        lastBlockHeight = max(keyValues)

        # query neo4j: check if block is inserted
        query = f"""MATCH (b:{block_label} {{height: {lastBlockHeight}}}) RETURN b"""
        result = session.run(query).values()

        found = False
        while found == False:
            if result == []:
                time.sleep(60)
                result = session.run(query).values()
            else:
                found = True


        # check transaction offset
        stream = os.popen(f"kafka-run-class kafka.tools.GetOffsetShell --broker-list localhost:9092 --time -1 --topic {transaction_topic}")
        output = stream.read().strip().split('\n')


        for i in range(len(output)):
            output[i] = output[i].split(':')


        positions = []
        transactions = []
        
        for i in range(len(output)):
            partition = int(output[i][1])
            if int(output[i][2]) != 0:
                offset = int(output[i][2]) - 1
                stream = os.popen(f"kafka-console-consumer --bootstrap-server localhost:9092   --topic {transaction_topic}                                       --partition {partition}  --offset {offset} --property print.key=true  --max-messages 1")
                outputs = stream.read().strip().split('\t')


                block = int((outputs[0].split('_'))[0])
                position = int((outputs[0].split('_'))[1])
                txid = json.loads(outputs[1])
                transaction = txid["txid"]

                #get only the transaction which pertain to the same blockheight as maxBlockHeight
                if block == lastBlockHeight:
                    positions.append(position)
                    transactions.append(transaction)



        # position of the last transaction inserted into kafka
        lastPosition = max(positions)
        lastPositionIndex = positions.index(lastPosition)
        lastTransaction = transactions[lastPositionIndex]


        query = f"""MATCH (t:{transaction_label}) WHERE t.txid = '{lastTransaction}' RETURN t"""
        result = session.run(query).values()

        found = False
        while found == False:
            if result == []:
                time.sleep(60)
                result = session.run(query).values()
            else:
                found = True


        #check if the the last transaction inserted into Kafka is the last transaction of the list from last block
        blockhash   = getBlockHash(lastBlockHeight)
        key, data, block = getBlock(blockhash)
        nTx = block['nTx']
        if lastPosition != nTx -1:
            # start kafkaProducer to insert the remaining transactions
            txOffset = lastPosition + 1
            kafkaProducer(lastBlockHeight, block_topic, transaction_topic, True, False, txOffset)
            
    print("Finish 3 ")



            
# Start Main Logic

# get latest block in neo4j 
query = f"""MATCH (b:{block_label}) WHERE EXISTS(b.height) RETURN b.height ORDER BY b.height DESC LIMIT 1"""

result = session.run(query)
currentBlock = result.values()[0][0]

endNeo4jConnection(session,driver)


# get latest block in blockchain
latestBlock = getLatestBlockHeight()
print("Ltest Block ", latestBlock )

# block is legit to be inserted in kafka&neo4j when there are 6 confirmations
offset = 6
while True:
    if currentBlock < latestBlock-offset: 
        currentBlock = currentBlock + 1
        kafkaProducer(currentBlock, block_topic, transaction_topic, True, True, 0)
    else:
        time.sleep(300)
        latestBlock = getLatestBlockHeight()
    


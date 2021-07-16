#!/usr/bin/env python
# coding: utf-8

# import packages

import sys
from kafka import KafkaProducer
sys.path.append("../")
from bitcoin_rpc import *


def kafkaProducer(startBlock, endBlock, blockTopic, transactionTopic, getInput):
   
    producer = KafkaProducer(bootstrap_servers='localhost:9092')
    producer = KafkaProducer(value_serializer=lambda v: json.dumps(v).encode('utf-8'))
    
    for blockheight in range(startBlock, endBlock):
        
        try:
            # retrival of block + transfer to the respective topic
            blockhash = getBlockHash(blockheight)
            data, block = getblock(blockhash)
            producer.send(blockTopic, data)
            
        except:
            print('Error handling block at height' + str(blockheight) + 'with blockhash' + str(blockhash))
    

        # retrival of transactions + transfer to the respective topic
        for txid in block['tx'][:]:
            try:
                tx = gettx(txid,block,getInput)
                producer.send(transactionTopic, tx)
            except:
                print('Error handling transactions at block' + str(blockheight) + ' with transaction id' + str(txid['txid']))


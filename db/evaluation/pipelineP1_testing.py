#!/usr/bin/env python
# coding: utf-8

from bitcoin_rpc import * 
import json
from kafka import KafkaProducer
producer = KafkaProducer(bootstrap_servers='localhost:9092')
producer = KafkaProducer(value_serializer=lambda v: json.dumps(v).encode('utf-8'))


startTime = time.time()

for blockheight in range(1,11):
    
    # retrival of block + transfer to respective topic 
    blockhash = getBlockHash(blockheight)
    data, block = getblock(blockhash)
    producer.send('blocks', data)
   
    
    # retrival of transactions + transfer to respective topic
    for txid in block['tx'][:]:
        try:
            #print(txid)
            tx = gettx(txid,block)
            producer.send('transactions', tx)
        except:
            print("Error handling transactions at block" + str(blockheight) + ' with transaction id' + str(txid['txid']))


endTime = (time.time() - startTime)
print('Execution time in seconds: ' + str(endTime))
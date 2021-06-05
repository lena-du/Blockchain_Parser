#!/usr/bin/env python
# coding: utf-8

from bitcoin_rpc import * 
import json
from kafka import KafkaProducer
producer = KafkaProducer(bootstrap_servers='localhost:9092')
producer = KafkaProducer(value_serializer=lambda v: json.dumps(v).encode('utf-8'))


startTime = time.time()

for blockheight in range(1,11):
    try:
        # retrival of block + transfer to respective topic 
        blockhash = getBlockHash(blockheight)
        data, block = getblock(blockhash)
        producer.send('blocks', data)
    except:
        print("Error handling block at length" + str(blockheight)
    
    try:
        # retrival of transactions + transfer to respective topic
        for txid in block['tx'][:]:
            tx = gettx(txid,block)
            producer.send('transactions', tx)
    except:
        print("Error handling transactions at block" + str(blockheight) + ' with transaction id' + str(txid))


endTime = (time.time() - startTime)
print('Execution time in seconds: ' + str(endTime))
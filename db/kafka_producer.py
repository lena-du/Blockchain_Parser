#!/usr/bin/env python
# coding: utf-8

import sys
from kafka import KafkaProducer
sys.path.append("../")
from bitcoin_rpc import *


# send block and transaction objects to Kafka - starting from txOffset in case only a part of transactions of the list were sent to Kafka 
def kafkaProducer(blockHeight, blockTopic, transactionTopic, getInput, importBlock, txOffset):
    
    producer = KafkaProducer(bootstrap_servers='localhost:9092')
    
    try:
        # retrival of block + send to the respective topic
        blockhash = getBlockHash(blockHeight)
        blockkey, blockdata, block = getBlock(blockhash)
        
        # only send to Kafka if this is set to True
        if importBlock: 
            j_blockdata = json.dumps(blockdata).encode("utf-8")
            producer.send(blockTopic, key=str(blockkey).encode('utf-8'), value=j_blockdata)
            producer.flush()
    except:
        print('Error handling block at height ' + str(blockHeight) + ' with blockhash ' + str(blockhash))
        
    for i in range(txOffset, len(block['tx'])): 
        tx = block['tx'][i]
        txid = tx['txid']
        try: 
            blockheight, txdata = getTx(tx,block,getInput)
            txkey = f"{blockheight}_{i}"
            j_txdata = json.dumps(txdata).encode("utf-8")
            producer.send(transactionTopic, key=txkey.encode('utf-8') , value=j_txdata)
        except:
            print('Error handling transactions at block ' + str(blockHeight) + ' with transaction id ' + txid)

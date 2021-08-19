#!/usr/bin/env python
# coding: utf-8

# # directNeo4jImporter

 
# This file is used to directly push blocks and transactions (incl. addresses to neo4j)


# imports
import sys
from cypher_queries import *
sys.path.append("../")
from bitcoin_rpc import *
from neo4jConnector import startNeo4jSession


def directNeoImport(startBlock, endBlock, kafka_topics, node_labels, evaluate_original, 
                    run_tx, create_block, queryBlocks, queryTransactions, driver, session):

    
    
    for blockheight in range(startBlock,endBlock):
        try:
            # retrival of block + transfer to the respective topic
            blockhash = getBlockHash(blockheight)
            key, data, block = getBlock(blockhash)
            
            # push to neo4j
            with driver.session() as session:
                session.write_transaction(create_block, data)
            
            
        except:
            print('Error handling block at height' + str(blockheight) + 'with blockhash' + str(blockhash))
    

        # retrival of transactions + transfer to the respective topic
        for txid in block['tx'][:]:
            try:
                blockheight, tx = getTx(txid,block,True)
                
                # push to neo4j
                with driver.session() as session:
                    session.write_transaction(run_tx, tx)
                
            except:
                print('Error handling transactions at block' + str(blockheight) + ' with transaction id' + str(txid['txid']))

    return 


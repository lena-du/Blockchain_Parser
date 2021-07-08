#!/usr/bin/env python
# coding: utf-8

# # Deleting nodes

# ## Imports


import numpy as np
import sys
import sys
sys.path.append("../")
from bitcoin_rpc import *
#sys.path.append('./evaluation')
from neo4jConnector import startNeo4jSession


# ## Deletion Functions
# ### Test Node Deletion



def deleteTestEvaluationNodes(node_labels,
                              neo4j_location = 'server', 
                              neo4j_port = '7687'):
    
    driver, session = startNeo4jSession(location=neo4j_location, port=neo4j_port)

    # loop through all thre node types / labels
    for label in node_labels['test'].keys():
        
        # delet nodes        
        session.run(f'MATCH (n:{label}) DETACH DELETE n')
    
    session.close()
    driver.close()


# ### Original Node Deletion
# #### Node Retrieval


def getNodes(start_block_height, end_block_height):

    # lists of nodes to delete
    deletion_blocks       = []
    deletion_transactions = []
    deletion_addresses    = []

    for blockheight in range(start_block_height, end_block_height):

        # retrival of block + transfer to respective topic 
        blockhash = getBlockHash(blockheight)
        data, block = getblock(blockhash)

        # add blocks
        deletion_blocks.append(block['hash'])

        # retrival of transactions + transfer to respective topic
        for tx in block['tx'][:]:

            try:
                # retrieve transaction information
                tx = gettx(tx,block)
                # add transaction nodes
                deletion_transactions.append(tx['txid'])

                # add all address nodes
                outputs   = tx['output_list']
                addresses = [i['addr'] for i in outputs]
                for address in addresses:
                    deletion_addresses.append(address)

            except:
                print("Error handling transactions at block" + str(blockheight) + ' with transaction id' + str(txid['txid']))
    
    # deduplicate addresses
    deletion_addresses = list(set(deletion_addresses))
    
    return deletion_blocks, deletion_transactions, deletion_addresses


# checking, which of the addresses are not already in the db
def checkAddresses(neo4j_location, neo4j_port, label_address, deletion_addresses):
    # create connection to neo4j
    driver, session = startNeo4jSession(location=neo4j_location, port=neo4j_port)

    # list of addresses that need to be deleted after each run
    new_addresses = []

    for address in deletion_addresses:

        # check if address already exists
        result = session.run(f'MATCH (a:{label_address} {{address: \'{address}\'}}) RETURN a').data()

        # if query result is empty -> addresses will be newly created
        if result == []:
            new_addresses.append(address)
    
    session.close()
    driver.close()

    return new_addresses


def getDeletionList(start_block_height, 
                    end_block_height, 
                    label_address,
                    neo4j_location = 'server', 
                    neo4j_port = '7687'):
    
    deletion_blocks, deletion_transactions, deletion_addresses = getNodes(start_block_height, end_block_height)
    
    deletion_addresses = checkAddresses(neo4j_location, neo4j_port, label_address, deletion_addresses)
    
    deletion_nodes = {}
    deletion_nodes['block']       = deletion_blocks
    deletion_nodes['transaction'] = deletion_transactions
    deletion_nodes['address']     = deletion_addresses
    
    return deletion_nodes


# #### Node Deletion

def deleteOriginalEvaluationNodes(deletion_nodes, 
                                  node_labels,
                                  neo4j_location = 'server', 
                                  neo4j_port = '7687'):
    
    # connect to Neo4j
    driver, session = startNeo4jSession(location=neo4j_location, port=neo4j_port)
    
    # loop through all nodes
    for node_type in deletion_nodes.keys():
        label     = node_labels['original'][node_type]
        node_list = deletion_nodes[node_type]
        
        if node_type == 'block':
            identifying_property = 'hash'
        elif node_type == 'transaction':
            identifying_property = 'txid'
        elif node_type == 'address':
            identifying_property = 'address'
        
        # delet nodes
        for identifier in node_list:
            session.run(f'MATCH (n:{label} {{{identifying_property}: \'{identifier}\'}}) DETACH DELETE n')
    
    session.close()
    driver.close()


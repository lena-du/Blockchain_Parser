#!/usr/bin/env python
# coding: utf-8

# # Correctness Test

# ## Set up

import numpy as np
import pandas as pd
import time
from neo4jConnector import startNeo4jSession


# ## Analysis

# ### Functions
# 
# #### Queries

### Blocks
## properties
def getBlockPropertiesByHeightQuery(blockClasses, height):
    return f'''
            MATCH (b:{blockClasses[0]} {{height: {height}}}) 
            WITH COLLECT([b.height, b.blockDate, b.hash, b.mediantime]) as properties
            RETURN apoc.util.md5(properties), properties
            UNION
            MATCH (b:{blockClasses[1]} {{height: {height}}}) 
            WITH COLLECT([b.height, b.blockDate, b.hash, b.mediantime]) as properties
            RETURN apoc.util.md5(properties), properties
            '''

###  Transactions
## retrieve transaction ids from block
def getTransactionsFromBlockHeightQuery(blockClasses, height):
    return f'''
            MATCH (b:{blockClasses[0]} {{height: {height}}})<-[:BELONGS_TO]-(t) 
            WITH t.txid as txids WITH txids ORDER BY txids WITH COLLECT(txids) as list 
            RETURN apoc.util.md5(COLLECT(list)), list
            UNION
            MATCH (b:{blockClasses[1]} {{height: {height}}})<-[:BELONGS_TO]-(t) 
            WITH t.txid as txids WITH txids ORDER BY txids WITH COLLECT(txids) as list 
            RETURN apoc.util.md5(COLLECT(list)), list
            '''

## TR properties
def getTransactionPropertiesByTxidQuery(transactionClasses, txid):
    return f'''
            MATCH (t:{transactionClasses[0]} {{txid: \"{txid}\"}}) 
                WITH COLLECT([t.txid, t.inDegree, t.outDegree, t.inSum, t.outSum, t.date]) as properties 
                RETURN apoc.util.md5(properties), properties
            UNION
            MATCH (t:{transactionClasses[1]} {{txid: \"{txid}\"}}) 
                WITH COLLECT([t.txid, t.inDegree, t.outDegree, t.inSum, t.outSum, t.date]) as properties 
                RETURN apoc.util.md5(properties), properties
            '''                                 


# TR edges with edgetype, value & address
# in case of need to also separately retrieve list of addresses
'''
MATCH (t:{transactionClasses[1]} {{txid: \"{txid}\"}})-[r:SENDS|RECEIVES]-(a) 
    WITH type(r) AS type, r.value AS value, a.address AS address
    WITH type, value, address ORDER BY type, value, address
    WITH COLLECT([type, value, address]) AS edges, COLLECT(address) AS addresses
    RETURN apoc.util.md5(COLLECT(edges)), edges, addresses
'''
#
def getAddressFromTransactionIDQuery(transactionClasses, txid):
    return f'''
            MATCH (t:{transactionClasses[0]} {{txid: \"{txid}\"}})-[r:SENDS|RECEIVES]-(a) 
                WITH type(r) AS type, r.value AS value, a.address AS address
                WITH type, value, address ORDER BY type, value, address
                WITH COLLECT([type, value, address]) AS edges
                RETURN apoc.util.md5(COLLECT(edges)), edges
            UNION
            MATCH (t:{transactionClasses[1]} {{txid: \"{txid}\"}})-[r:SENDS|RECEIVES]-(a) 
                WITH type(r) AS type, r.value AS value, a.address AS address
                WITH type, value, address ORDER BY type, value, address
                WITH COLLECT([type, value, address]) AS edges
                RETURN apoc.util.md5(COLLECT(edges)), edges
            '''



# #### Other functions

# other functions 

def runQuery(session, query):
    return session.run(query).values()


## second version 
def matchProperties(session,
                    nodeClassList, 
                    query,
                    node_identifier, 
                    match_count, 
                    mismatches):
    
    #send query to neo4j
    try:
        result = runQuery(session, query(nodeClassList, node_identifier))
    except:
        raise Exception('Neo4j query aborted.')

    # match
    if len(result) == 1:
        match_count += 1
    
    # mismatch
    elif len(result) == 2:
         # todo: extend outputs to dictionary containing all relevant characters
        outputs                              = {}
        outputs['node_type']                 = nodeClassList[0]
        outputs['node_identifier']           = node_identifier
        outputs['query']                     = query.__name__
        outputs['cyperQuery']                = query(nodeClassList, node_identifier)
        outputs[nodeClassList[0]+'_outputs'] = result[0][-1]
        outputs[nodeClassList[1]+'_outputs'] = result[1][-1]
        
        mismatches.append(outputs)
    
    # something went wrong
    else:
        raise Exception('Length of query output does not match.')
        
    # return match_count, mismatches and all results without the hash
    return match_count, mismatches, result[0][-1]



# ending connection
def endNeo4jConnection(session, driver):
    session.close()
    driver.close()
    return
  

    
# mismatch analysis
def analyseMismatches(mismatches, experimentRun, printMismatches=False, saveMismatches=True):

    if printMismatches == True:
        count = 1
        for mismatch in mismatches:
            print(f'\n**************************************************************                     \nMismatch nr. {count}                     \n************************************************************** ')
            for item in mismatch:
                print('-', item)
                print('  ', mismatch[item])
                print('----------')
            count += 1 
        
    if saveMismatches == True:
        df = pd.DataFrame.from_dict(mismatches)
        if df.shape[0] > 0:
            path = f'./results/mismatches/mismatches_{experimentRun}.csv'
            df.to_csv(path, index=False)
            print(f' -- Mismatches saved to {path}')
        else:
            print(f' -- No Mismatches, no file saved')

    return




# ### Correctnes check


def checkCorrectness(start_block_height, 
                     end_block_height,
                     node_labels,
                     neo4j_port,
                     experimentRun, 
                     printMismatches=False, 
                     saveMismatches=True):

    # connect to neo4j
    driver, session = startNeo4jSession(port=neo4j_port)
    
    # overall parameter
    mismatches  = []
    match_count = 0 
    
    # node labels
    blockClasses       = [node_labels['original']['block'],       node_labels['test']['block']]
    transactionClasses = [node_labels['original']['transaction'], node_labels['test']['transaction']]
    addressClasses     = [node_labels['original']['address'],     node_labels['test']['address']]

    #timing
    startTime = time.time()

    #loop through blocks
    for block_height in np.arange(start_block_height, end_block_height):

        # check whether returned block properties match
        match_count, mismatches, outputs = matchProperties(session = session,
                                                           nodeClassList = blockClasses, 
                                                           query = getBlockPropertiesByHeightQuery,
                                                           node_identifier = block_height,
                                                           match_count = match_count,
                                                           mismatches = mismatches)

        # check whether returned txids  match
        match_count, mismatches, outputs = matchProperties(session = session,
                                                           nodeClassList = blockClasses, 
                                                           query = getTransactionsFromBlockHeightQuery,
                                                           node_identifier = block_height,
                                                           match_count = match_count,
                                                           mismatches = mismatches)

        # loop through all provided txids of the correct block
        for txid in outputs:

            # match tx properties
            match_count, mismatches, outputs = matchProperties(session = session,
                                                               nodeClassList = transactionClasses, 
                                                               query = getTransactionPropertiesByTxidQuery,
                                                               node_identifier = txid, 
                                                               match_count = match_count,
                                                               mismatches = mismatches)

            match_count, mismatches, outputs = matchProperties(session = session,
                                                               nodeClassList = transactionClasses, 
                                                               query = getAddressFromTransactionIDQuery,
                                                               node_identifier = txid, 
                                                               match_count = match_count,
                                                               mismatches = mismatches)


    testTime = np.round( ((time.time() - startTime)/60) ,2)
    print('\n## Correctnes Test ##')
    print(f' -- Test time in {testTime} minutes.')
    print( ' -- Retrieved blocks: ', 1 + block_height - start_block_height)
    print(f' -- Matches: {match_count}; Mismatches: {len(mismatches)}')
    
    # if wanted, print and save the mismatches
    analyseMismatches(mismatches, experimentRun, printMismatches, saveMismatches)    
    
    # close connection
    endNeo4jConnection(session, driver)
    
    return 


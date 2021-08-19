#!/usr/bin/env python
# coding: utf-8

# # Cypher Queries


# Convert final query by cutting all linebreaks...
def createCypherForEvents(query):
    new_query = query.replace('$', 'event.')
    return new_query

# Convert final query by cutting all linebreaks...
def omitSpacings(query):
    omit_characters = ["\n", "     ", "     ", "  "]
    for i in omit_characters:
        query = query.replace(i, " ")
    return query

# Get cypher query
def getCypherQueries(topic, evaluate_original, matchOnAddress, getTemplate, node_labels, evaluation):
    
    
    if evaluate_original == True:
        blockLabel       = node_labels['original']['block']
        transactionLabel = node_labels['original']['transaction']
        addressLabel     = node_labels['original']['address']
        
    else:
        blockLabel       = node_labels['test']['block']
        transactionLabel = node_labels['test']['transaction']
        addressLabel     = node_labels['test']['address']
    
    
    # ** Transaction **
    
    transactionQuery = f'''
        MERGE (t:{transactionLabel}{{txid: $txid}}) 
            SET t += {{inDegree: $inDegree, outDegree: $outDegree, outSum: $outSum, inSum: $inSum, date: date($block_date)}}

        MERGE (b:{blockLabel}{{hash: $block_hash}})
        MERGE (t)-[:BELONGS_TO]->(b)

        FOREACH (output in $output_list | 
            MERGE (o_a:{addressLabel}{{address: output.addr}}) 
                ON CREATE SET o_a += {{inDegree: 1, outDegree: 0}}
                ON MATCH  SET o_a += {{inDegree: o_a.inDegree + 1}}
            MERGE (t)-[r:RECEIVES{{output_nr: output.outNr, value: output.val}}]->(o_a))

        FOREACH (input in $input_list | 
            MERGE (i_a:{addressLabel}{{address: input.addr}})
                ON CREATE SET i_a += {{inDegree: 0, outDegree: 1}}
                ON MATCH SET  i_a += {{outDegree: i_a.outDegree + 1}}
            MERGE (i_a)-[:SENDS{{value: input.val}}]->(t))
        '''
    
    # Query for evaluation: 
    # - including creation time
    transactionQueryEvaluation = f'''
    MERGE (t:{transactionLabel}{{txid: $txid}}) 
        SET t += {{creationTime:apoc.date.currentTimestamp(), inDegree: $inDegree, outDegree: $outDegree, outSum: $outSum, inSum: $inSum, date: date($block_date)}}

    MERGE (b:{blockLabel}{{hash: $block_hash}})
    MERGE (t)-[:BELONGS_TO]->(b)
    
    FOREACH (output in $output_list | 
        MERGE (o_a:{addressLabel}{{address: output.addr}}) 
            ON CREATE SET o_a += {{creationTime:apoc.date.currentTimestamp(), inDegree: 1, outDegree: 0}}
            ON MATCH  SET o_a += {{inDegree: o_a.inDegree + 1}}
        MERGE (t)-[r:RECEIVES{{output_nr: output.outNr, value: output.val}}]->(o_a))
        
    FOREACH (input in $input_list | 
        MERGE (i_a:{addressLabel}{{address: input.addr}})
            ON CREATE SET i_a += {{creationTime:apoc.date.currentTimestamp(), inDegree: 0, outDegree: 1}}
            ON MATCH SET  i_a += {{outDegree: i_a.outDegree + 1}}
        MERGE (i_a)-[:SENDS{{value: input.val}}]->(t))
    '''

    
    # Query for evaluation: 
    # - including creation time 
    # - including matching on previous transaction
    # ! only works on consecutive chain !
    
    
    transactionQueryMatchTx = f'''
    MERGE (t:{transactionLabel}{{txid: $txid}}) 
        SET t += {{creationTime:apoc.date.currentTimestamp(), inDegree: $inDegree, outDegree: $outDegree, outSum: $outSum, inSum: $inSum, date: date($block_date)}}

    MERGE (b:{blockLabel}{{hash: $block_hash}})
    MERGE (t)-[:BELONGS_TO]->(b)
    
    FOREACH (output in $output_list | 
        MERGE (o_a:{addressLabel}{{address: output.addr}}) 
            ON CREATE SET o_a += {{creationTime:apoc.date.currentTimestamp(), inDegree: 1, outDegree: 0}}
            ON MATCH  SET o_a += {{inDegree: o_a.inDegree + 1}}
        MERGE (t)-[r:RECEIVES{{output_nr: output.outNr, value: output.val}}]->(o_a))
        
    FOREACH (input in $input_list | 
        FOREACH (_ IN CASE WHEN EXISTS(input.addr) THEN [1] ELSE [] END |    
            MERGE (i_a:{addressLabel}{{address: input.addr}})
                ON CREATE SET i_a += {{creationTime:apoc.date.currentTimestamp(), inDegree: 0, outDegree: 1}}
                ON MATCH SET  i_a += {{outDegree: i_a.outDegree + 1}}
            MERGE (i_a)-[:SENDS{{value: input.val}}]->(t)) 
        FOREACH (_ IN CASE WHEN EXISTS(input.txid) THEN [1] ELSE [] END |
            MERGE (i_tx:{transactionLabel}{{txid: input.txid}})
                  -[i_r:RECEIVES{{output_nr: input.outNr}}]->
                  (i_a:{addressLabel})
                ON MATCH SET  i_a += {{outDegree: i_a.outDegree + 1}}
            MERGE (i_a)-[:Sends{{value: i_r.value}}]->(t)) )
            
    '''
    
    # overriding actual query to test on incomplete chain 
    # last foreach statement changed
    transactionQueryMatchTx = f'''
    MERGE (t:{transactionLabel}{{txid: $txid}}) 
        SET t += {{creationTime:apoc.date.currentTimestamp(), inDegree: $inDegree, outDegree: $outDegree, outSum: $outSum, inSum: $inSum, date: date($block_date)}}

    MERGE (b:{blockLabel}{{hash: $block_hash}})
    MERGE (t)-[:BELONGS_TO]->(b)
    
    FOREACH (output in $output_list | 
        MERGE (o_a:{addressLabel}{{address: output.addr}}) 
            ON CREATE SET o_a += {{creationTime:apoc.date.currentTimestamp(), inDegree: 1, outDegree: 0}}
            ON MATCH  SET o_a += {{inDegree: o_a.inDegree + 1}}
        MERGE (t)-[r:RECEIVES{{output_nr: output.outNr, value: output.val}}]->(o_a))
        
    FOREACH (input in $input_list | 
        FOREACH (_ IN CASE WHEN EXISTS(input.addr) THEN [1] ELSE [] END |    
            MERGE (i_a:{addressLabel}{{address: input.addr}})
                ON CREATE SET i_a += {{creationTime:apoc.date.currentTimestamp(), inDegree: 0, outDegree: 1}}
                ON MATCH SET  i_a += {{outDegree: i_a.outDegree + 1}}
            MERGE (i_a)-[:SENDS{{value: input.val}}]->(t)) 
        FOREACH (_ IN CASE WHEN EXISTS(input.txid) THEN [1] ELSE [] END |
            MERGE (i_tx:{transactionLabel}{{txid: input.txid}})
                  -[i_r:RECEIVES{{output_nr: input.outNr}}]->
                  (i_a:{addressLabel})
                ON MATCH SET  i_a += {{outDegree: i_a.outDegree + 1}} 
            MERGE (i_a)-[s_i_a:Sends]->(t)
                ON MATCH SET s_i_a = {{value: i_r.value + 1}} ) )
            
    '''
    #//-[:Sends{{value: i_r.value}}]->(t)
    
    # ** Block **
    
    blockQuery = f'''
        MERGE (p:{blockLabel} {{hash: $previousblockhash}})
        MERGE (b:{blockLabel} {{hash: $block_hash}}) 
            SET b += {{hash: $block_hash, height: $block_height, blockDate: date($block_date), mediantime: datetime($block_median_time) }}
        MERGE (p)-[r:PRECEDES]->(b)
        '''
    
    # Query for evaluation: 
    # - including creation time
    blockQueryEvaluation = f'''
        MERGE (p:{blockLabel} {{hash: $previousblockhash}})
        MERGE (b:{blockLabel} {{hash: $block_hash}}) 
            SET b += {{creationTime:apoc.date.currentTimestamp(), hash: $block_hash, height: $block_height, blockDate: date($block_date), mediantime: datetime($block_median_time) }}
        MERGE (p)-[r:PRECEDES]->(b)
        '''
    
    # check which query to return
    if topic == 'transactions':
        
        if evaluation == False:
            
            if matchOnAddress == True:
                query_to_return = transactionQuery

        elif evaluation == True:
            
            if matchOnAddress == True:
                query_to_return = transactionQueryEvaluation
            elif matchOnAddress == False:
                query_to_return = transactionQueryMatchTx
        
    elif topic == 'blocks':
        
        if evaluation == False:
            query_to_return = blockQuery

        elif evaluation == True:
            query_to_return = blockQueryEvaluation
                
    else:
        raise Exception('Topics not matching queries')

    
    if getTemplate == True:
        query_to_return = omitSpacings(createCypherForEvents(query_to_return))
    
    
    return query_to_return



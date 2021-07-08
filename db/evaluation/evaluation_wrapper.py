#!/usr/bin/env python
# coding: utf-8

# # Evaluation Wrapper

# ## Parameter
# 
# #### General Parameter

## put in settings(?)
node_labels = {
    'original': {
        'block'       : 'Block',
        'transaction' : 'Transaction',
        'address'     : 'Address'
    },
    'test': {
        'block'       : 'Block_test',
        'transaction' : 'Transaction_test',
        'address'     : 'Address_test'
    }
}

neo4j_port = str(7687)


# #### Changing Parameter

# set to false if test_nodes are inserted # Todo -> change to empty vs uptodate DB ?
evaluate_original = False

# block heights
if evaluate_original == True:
    start_block_height = 600000  # check
    end_block_height   = start_block_height + 10
else:
    start_block_height = 1 
    end_block_height   = start_block_height + 100

kafka_partitions = [1,2,4,8]

check_correctness = False



# create table of all settings 
# for each set of settings (for each experiment run) make counter
# -> experimentRun
# (hand over to mismachtches)
experimentRun = 1


# ## Imports

# In[ ]:


import os

from node_deletion import *
from correctness_test import *


# ## Testing Process
# 
# ### Preparation



# create directory structure
result_dir     = 'results'
mismatches_dir = 'mismatches'
if os.path.exists(result_dir) == False:
    os.makedirs(result_dir)
if os.path.exists(os.path.join(result_dir, mismatches_dir)) == False:
    os.makedirs(os.path.join(result_dir, mismatches_dir))
    


# collect original nodes that need to be deleted
if evaluate_original == True:
    
    # ToDo: check correctness of starting hight
    # #query neo4j if 


    # collecting nodes for 
    deletion_nodes = getDeletionList(start_block_height = start_block_height, 
                                     end_block_height = end_block_height, 
                                     label_address = node_labels['original']['address'], 
                                     neo4j_location = 'server', 
                                     neo4j_port = '7687')



# set kafka partitions
#...


# ### Insertion & Performance Testing

# ### Correctness Testing
# 

if evaluate_original == False and check_correctness == True:
    checkCorrectness(start_block_height, 
                     end_block_height,
                     node_labels,
                     neo4j_port,
                     experimentRun, 
                     printMismatches=False, 
                     saveMismatches=True)

    
# ### Deletion of inserted nodes


# comment out to enable deletion
'''
if evaluate_original == True:
    deleteOriginalEvaluationNodes(deletion_nodes = deletion_nodes, 
                                  node_labels = node_labels,
                                  neo4j_location = 'server', 
                                  neo4j_port = '7687')
else:
    deleteTestEvaluationNodes(node_labels = node_labels,
                              neo4j_location = 'server', 
                              neo4j_port = '7687')
'''


# ## Evaluation Process cleanup
# 
# Restore streams file
# - remove insertion time






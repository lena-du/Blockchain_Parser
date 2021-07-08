#!/usr/bin/env python
# coding: utf-8

# # Evaluation Wrapper

# ## Parameter

# In[ ]:


##  omit
# node labels
label_block       = 'Block'
label_transaction = 'Transaction'
label_address     = 'Address'

# test note labels
label_test_block       = label_block + '_test'
label_test_transaction = label_transaction + '_test'
label_test_address     = label_address + '_test'


# block heights
start_block_height = 1
end_block_height   = 10


# In[ ]:


## put in settings
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


# In[ ]:


from node_deletion import *


# In[ ]:


getDeletionList(start_block_height = start_block_height, 
                end_block_height = end_block_height, 
                label_address = node_labels['original']['address'], 
                neo4j_location = 'server', 
                neo4j_port = '7687')


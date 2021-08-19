#!/usr/bin/env python
# coding: utf-8

# # Setup for BITCOIN-SYNC
# Please execute once to set up everything

import os
import json

settings_file_name = 'settings.json'

# read in settings
with open(settings_file_name) as json_file:
    settings = json.load(json_file)

# read absolute paths
path_to_settings       = settings['path_to_settings']
path_to_neo4j_conf_dir = settings['path_to_neo4j_conf_dir']

# copy example streams.conf file to correct directory.
os.popen(f'cp streams.conf {path_to_neo4j_conf_dir}/streams.conf')





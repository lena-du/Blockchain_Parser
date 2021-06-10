#!/usr/bin/env python
# coding: utf-8

# # Function to start neo4j session

from neo4j import GraphDatabase
import pandas as pd


def startNeo4jSession(path_to_credentisls = '../credentialsNeo4j.json',
                      location = 'server',   # create settings file, retrieve from these
                      port = 7687):          # same here
    
    credentialsNeo4j = pd.read_json(path_to_credentisls)

    uri = "neo4j://localhost:" + str(port)

    if location not in ['local', 'server']:
        raise Exception('Location has to be set to \'server\' or \'local\'')

    username = credentialsNeo4j[location][0]['user']
    password = credentialsNeo4j[location][0]['pwd']
    
    driver = GraphDatabase.driver(uri, auth=(username, password))
    session = driver.session()
    return driver, session
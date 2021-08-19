#!/usr/bin/env python
# coding: utf-8

# # Function to start & stop neo4j session

from neo4j import GraphDatabase
import pandas as pd
import os


def startNeo4jSession(credentials  = './credentialsNeo4j.json',
                      location = 'server',  
                      port = 7687,
                      settings_path = './'):
    
    try:
        credentialsNeo4j = pd.read_json(credentials)
    except:
        try:
            credentialsNeo4j = pd.read_json(os.path.join(settings_path, credentials[2:]))
        except:
            raise Exception('credentials could not be found')

    uri = "neo4j://localhost:" + str(port)

    if location not in ['local', 'server']:
        raise Exception('Location has to be set to \'server\' or \'local\'')

    username = credentialsNeo4j[location][0]['user']
    password = credentialsNeo4j[location][0]['pwd']
    
    driver = GraphDatabase.driver(uri, auth=(username, password))
    session = driver.session()
    return driver, session

def endNeo4jConnection(session, driver):
    session.close()
    driver.close()
    return
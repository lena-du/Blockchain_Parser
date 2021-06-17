import os 
import time
import json
import hashlib
from base58 import b58encode
from binascii import unhexlify
from kafka import KafkaProducer
from datetime import datetime, timezone


def getBestBlockHash():
    # get best blockhash - returns the header hash of the most recent block on the best block chain
    stream = os.popen('bitcoin-cli getblockchaininfo')
    output = stream.read()
    blockchaininfo = json.loads(output)
    bestblockhash = blockchaininfo['bestblockhash']
    return bestblockhash


def getBlockHash(height):
    stream = os.popen(f"bitcoin-cli getblockhash {height}")
    output = stream.read().strip()
    return output


def getblock(blockhash):
    command = "bitcoin-cli getblock " + blockhash + " 2"
    stream = os.popen(command)
    block = json.loads(stream.read())

    # filter relevant blockinfo
    from datetime import datetime, timezone
    ts_median = block['time']
    block_timestamp = datetime.fromtimestamp(ts_median, tz=timezone.utc)
    block_median_time = block_timestamp.strftime('%Y-%m-%dT%H:%M')
    block_date = block_timestamp.strftime('%Y-%m-%d')
    block_hash = block['hash']
    block_height = block['height']
    # handling genesis block
    if block_height != 0:
        previousblockhash = block['previousblockhash']

    # build json object
    data = {}
    data['block_hash'] = block_hash
    data['block_height'] = block_height
    data['block_median_time'] = str(block_median_time)
    data['block_date'] = str(block_date)
    if block_height != 0:
        data['previousblockhash'] = previousblockhash

    return data, block

def gettx(tx,block): 
    command = "bitcoin-cli getrawtransaction " + tx['txid'] + " true"
    stream = os.popen(command)

    # load data into json object rawtx
    rawtx = json.loads(stream.read())

    txdata = {}
    txdata['txid'] = tx['txid']
    txdata['block_hash'] = block['hash']
    ts_epoch = block['time']
    block_timestamp = datetime.fromtimestamp(ts_epoch, tz=timezone.utc)
    block_date = block_timestamp.strftime('%Y-%m-%d')
    txdata['block_date'] = str(block_date) # need to check with neo4j

    addr = ""
    val = 0
    outSum = 0
    inSum = 0
    inputAddrObject = {}
    outputAddrObject = {}
    input_address_list = []
    output_address_list = []

    ## check coinbase
    if 'coinbase' not in rawtx['vin'][0]:
        for i in rawtx['vin']:
            command = "bitcoin-cli getrawtransaction " + i['txid'] + " true"
            inputstream = os.popen(command)
            inputtx = json.loads(inputstream.read())
            inputtx_json_data = json.dumps(inputtx, indent=4, sort_keys=False)
            val = round(inputtx['vout'][i['vout']]['value']*100000000)
            inSum += val

            # input addresses - P2PK
            if inputtx['vout'][i['vout']]['scriptPubKey']['type'] == "pubkey":
                ia = getAddress(inputtx['vout'][i['vout']]['scriptPubKey']['asm'].split()[0])
                inputAddrObject['addr'] = ia.decode("utf-8")
                inputAddrObject['val'] = val  

                jInAddr = json.dumps(inputAddrObject)
                jsonInDict = json.loads(jInAddr)
                input_address_list.append(jsonInDict)

            # P2PKH
            if 'addresses' in inputtx['vout'][i['vout']]['scriptPubKey']:
                for ia in inputtx['vout'][i['vout']]['scriptPubKey']['addresses']:
                    inputAddrObject['addr'] = ia
                    inputAddrObject['val'] = val

                    jInAddr = json.dumps(inputAddrObject)
                    jsonInDict = json.loads(jInAddr)
                    input_address_list.append(jsonInDict)

        # output addresses
        for o in rawtx['vout']:
            if o['scriptPubKey']['type'] != "nulldata": # handling OP_RETURN data - can be skipped
                outSum += o['value']*100000000
                if o['scriptPubKey']['type'] == "pubkey":
                    a = getAddress(o['scriptPubKey']['asm'].split()[0] )
                    outputAddrObject['addr'] = a.decode("utf-8")
                    outputAddrObject['val'] =round(o['value']*100000000)
                    outputAddrObject['outNr'] = o['n']
                    
                    jOutAddr = json.dumps(outputAddrObject)
                    jsonOutDict = json.loads(jOutAddr)
                    output_address_list.append(jsonOutDict)
                if 'addresses' in o['scriptPubKey']:
                    for a in o['scriptPubKey']['addresses']:
                        outputAddrObject['addr'] = a
                        outputAddrObject['val'] =round(o['value']*100000000)
                        outputAddrObject['outNr'] = o['n']

                        jOutAddr = json.dumps(outputAddrObject)
                        jsonOutDict = json.loads(jOutAddr)
                        output_address_list.append(jsonOutDict)
                        break
    else:
        for o in rawtx['vout']:
            if o['scriptPubKey']['type'] != "nulldata": # handling OP_RETURN data - can be skipped
                outSum += o['value']*100000000
                if o['scriptPubKey']['type'] == "pubkey":
                    a = getAddress(o['scriptPubKey']['asm'].split()[0] )
                    outputAddrObject['addr'] = a.decode("utf-8")
                    outputAddrObject['val'] =round(o['value']*100000000)
                    outputAddrObject['outNr'] = o['n']
                if 'addresses' in o['scriptPubKey']:
                    for a in o['scriptPubKey']['addresses']:
                        outputAddrObject['addr'] = a
                        outputAddrObject['val'] =round(o['value']*100000000)
                        outputAddrObject['outNr'] = o['n']
                        break

        jOutAddr = json.dumps(outputAddrObject)
        jsonOutDict = json.loads(jOutAddr)
        output_address_list.append(jsonOutDict)
        inSum = round(outSum)
        inputAddrObject['addr'] = "coinbase"
        inputAddrObject['val'] = inSum

        jInAddr = json.dumps(inputAddrObject)
        jsonInDict = json.loads(jInAddr)
        input_address_list.append(jsonInDict)

    # get degrees
    txdata['outDegree'] = len(rawtx['vout'])
    txdata['inDegree'] = len(rawtx['vin'])
    txdata['outSum'] = round(outSum)
    txdata['inSum'] = inSum
    txdata['input_list'] = input_address_list
    txdata['output_list'] = output_address_list

    return txdata


def getAddress(pubKey):
    h3 = hashlib.sha256(unhexlify(pubKey))
    h4 = hashlib.new('ripemd160', h3.digest())

    result = b'\x00' + h4.digest()

    h5 = hashlib.sha256(result)
    h6 = hashlib.sha256(h5.digest())

    result += h6.digest()[:4]

    return b58encode(result)

def gettesttx(txid,block): 
    command = "bitcoin-cli getrawtransaction " + txid + " true"
    stream = os.popen(command)

    # load data into json object rawtx
    rawtx = json.loads(stream.read())

    txdata = {}
    txdata['txid'] = txid
    txdata['block_hash'] = block['hash']
    ts_epoch = block['time']
    block_timestamp = datetime.fromtimestamp(ts_epoch, tz=timezone.utc)
    block_date = block_timestamp.strftime('%Y-%m-%d')
    txdata['block_date'] = str(block_date) # need to check with neo4j

    addr = ""
    val = 0
    outSum = 0
    inSum = 0
    inputAddrObject = {}
    outputAddrObject = {}
    input_address_list = []
    output_address_list = []

    ## check coinbase
    if 'coinbase' not in rawtx['vin'][0]:
        for i in rawtx['vin']:
            command = "bitcoin-cli getrawtransaction " + i['txid'] + " true"
            inputstream = os.popen(command)
            inputtx = json.loads(inputstream.read())
            inputtx_json_data = json.dumps(inputtx, indent=4, sort_keys=False)
            val = round(inputtx['vout'][i['vout']]['value']*100000000)
            inSum += val

            # input addresses - P2PK
            if inputtx['vout'][i['vout']]['scriptPubKey']['type'] == "pubkey":
                ia = getAddress(inputtx['vout'][i['vout']]['scriptPubKey']['asm'].split()[0])
                inputAddrObject['addr'] = ia.decode("utf-8")
                inputAddrObject['val'] = val  

                jInAddr = json.dumps(inputAddrObject)
                jsonInDict = json.loads(jInAddr)
                input_address_list.append(jsonInDict)

            # P2PKH
            if 'addresses' in inputtx['vout'][i['vout']]['scriptPubKey']:
                for ia in inputtx['vout'][i['vout']]['scriptPubKey']['addresses']:
                    inputAddrObject['addr'] = ia
                    inputAddrObject['val'] = val

                    jInAddr = json.dumps(inputAddrObject)
                    jsonInDict = json.loads(jInAddr)
                    input_address_list.append(jsonInDict)

        # output addresses
        for o in rawtx['vout']:
            if o['scriptPubKey']['type'] != "nulldata": # handling OP_RETURN data - can be skipped
                outSum += o['value']*100000000
                if o['scriptPubKey']['type'] == "pubkey":
                    a = getAddress(o['scriptPubKey']['asm'].split()[0] )
                    outputAddrObject['addr'] = a.decode("utf-8")
                    outputAddrObject['val'] =round(o['value']*100000000)
                    outputAddrObject['outNr'] = o['n']
                    
                    jOutAddr = json.dumps(outputAddrObject)
                    jsonOutDict = json.loads(jOutAddr)
                    output_address_list.append(jsonOutDict)
                if 'addresses' in o['scriptPubKey']:
                    for a in o['scriptPubKey']['addresses']:
                        outputAddrObject['addr'] = a
                        outputAddrObject['val'] =round(o['value']*100000000)
                        outputAddrObject['outNr'] = o['n']

                        jOutAddr = json.dumps(outputAddrObject)
                        jsonOutDict = json.loads(jOutAddr)
                        output_address_list.append(jsonOutDict)
                        break
    else:
        for o in rawtx['vout']:
            if o['scriptPubKey']['type'] != "nulldata": # handling OP_RETURN data - can be skipped
                outSum += o['value']*100000000
                if o['scriptPubKey']['type'] == "pubkey":
                    a = getAddress(o['scriptPubKey']['asm'].split()[0] )
                    outputAddrObject['addr'] = a.decode("utf-8")
                    outputAddrObject['val'] =round(o['value']*100000000)
                    outputAddrObject['outNr'] = o['n']
                if 'addresses' in o['scriptPubKey']:
                    for a in o['scriptPubKey']['addresses']:
                        outputAddrObject['addr'] = a
                        outputAddrObject['val'] =round(o['value']*100000000)
                        outputAddrObject['outNr'] = o['n']
                        break

        jOutAddr = json.dumps(outputAddrObject)
        jsonOutDict = json.loads(jOutAddr)
        output_address_list.append(jsonOutDict)
        inSum = round(outSum)
        inputAddrObject['addr'] = "coinbase"
        inputAddrObject['val'] = inSum

        jInAddr = json.dumps(inputAddrObject)
        jsonInDict = json.loads(jInAddr)
        input_address_list.append(jsonInDict)

    # get degrees
    txdata['outDegree'] = len(rawtx['vout'])
    txdata['inDegree'] = len(rawtx['vin'])
    txdata['outSum'] = round(outSum)
    txdata['inSum'] = inSum
    txdata['input_list'] = input_address_list
    txdata['output_list'] = output_address_list

    return txdata




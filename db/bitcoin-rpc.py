import os 
import json
from datetime import datetime, timezone

def getBestBlockHash():
    # get best blockhash - returns the header hash of the most recent block on the best block chain
    stream = os.popen('bitcoin-cli getblockchaininfo')
    output = stream.read()
    blockchaininfo = json.loads(output)
    bestblockhash = blockchaininfo['bestblockhash']
    return bestblockhash

def getblock(blockhash):
    command = "bitcoin-cli getblock " + blockhash + " 2"
    stream = os.popen(command)
    block = json.loads(stream.read())

    # filter relevant blockinfo
    from datetime import datetime, timezone
    ts_median = block['mediantime']
    block_timestamp = datetime.fromtimestamp(ts_median)
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

def gettx(tx):

    command = "bitcoin-cli getrawtransaction " + tx['txid'] + " true"
    stream = os.popen(command)

    # load data into json object rawtx
    rawtx = json.loads(stream.read())

    txdata = {}
    txdata['txid'] = tx['txid']
    txdata['block_hash'] = block['hash']
    ts_epoch = block['time']
    block_timestamp = datetime.fromtimestamp(ts_epoch)
    block_date = block_timestamp.strftime('%Y-%m-%d')
    txdata['block_date'] = str(block_date)


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
            val = int (inputtx['vout'][i['vout']]['value']*100000000)
            inSum += val

            # input addresses
            for ia in inputtx['vout'][i['vout']]['scriptPubKey']['addresses']:
                inputAddrObject['addr'] = ia
                inputAddrObject['val'] = val

                jInAddr = json.dumps(inputAddrObject)
                jsonInDict = json.loads(jInAddr)
                input_address_list.append(jsonInDict)

        # output addresses
        for o in rawtx['vout']:
            if o['scriptPubKey']['type'] != "nulldata": # handling OP_RETURN data - can be skipped
                outSum += o['value']
                for a in o['scriptPubKey']['addresses']:
                    outputAddrObject['addr'] = a
                    outputAddrObject['val'] =int (o['value']*100000000)
                    outputAddrObject['outNr'] = o['n']

                    jOutAddr = json.dumps(outputAddrObject)
                    jsonOutDict = json.loads(jOutAddr)
                    output_address_list.append(jsonOutDict)
    else:
        for o in rawtx['vout']:
            if o['scriptPubKey']['type'] != "nulldata": # handling OP_RETURN data - can be skipped
                outSum += o['value']
                for a in o['scriptPubKey']['addresses']:
                    outputAddrObject['addr'] = a
                    outputAddrObject['outNr'] = o['n']

        jOutAddr = json.dumps(outputAddrObject)
        jsonOutDict = json.loads(jOutAddr)
        output_address_list.append(jsonOutDict)
        inSum = int(outSum*100000000)
        inputAddrObject['addr'] = "coinbase"
        inputAddrObject['val'] = inSum

        jInAddr = json.dumps(inputAddrObject)
        jsonInDict = json.loads(jInAddr)
        input_address_list.append(jsonInDict)


    # get degrees
    txdata['outDegree'] = len(rawtx['vout'])
    txdata['inDegree'] = len(rawtx['vin'])



    x = round(outSum*100000000, 0)
    txdata['outSum'] = int( x)
    txdata['inSum'] = inSum
    txdata['input_list'] = input_address_list
    txdata['output_list'] = output_address_list


    return txdata

#example block information retrieval
blockhash =   getBestBlockHash()
data, block = getblock(blockhash)
jsonBlockData = json.dumps(data, indent=4, sort_keys=False)
# tbd: send jsonBlockData to Kafka Blocks Topic
print(jsonBlockData)

# example transaction information retrieval
for id in block['tx'][:3]:
        tx = gettx(id)
        jsonTxData =  json.dumps(tx, indent=4, sort_keys=False)
        # tbd: send jsonTxData to Kafka Transactions Topic
        print(jsonTxData)
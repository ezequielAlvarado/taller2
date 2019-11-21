#
# Copyright 2010-2017 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# coding=utf-8


from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTShadowClient
import sys
import logging
import time
import json
import argparse
import os
import re

from AWSIoTPythonSDK.core.greengrass.discovery.providers import DiscoveryInfoProvider
from AWSIoTPythonSDK.core.protocol.connection.cores import ProgressiveBackOffCore
from AWSIoTPythonSDK.exception.AWSIoTExceptions import DiscoveryInvalidRequestException

from datetime import datetime
from flask import Flask, jsonify
from flask import render_template
import schemadb

app = Flask(__name__)       


MAX_DISCOVERY_RETRIES = 10    # MAX tries at discovery before giving up
GROUP_PATH = "./groupCA/"     # directory storing discovery info
CA_NAME = "root-ca.crt"       # stores GGC CA cert
GGC_ADDR_NAME = "ggc-host"    # stores GGC host address
temp="0"
humedad="0"
timestamp="1574190244"

# Shadow JSON schema:
#
# Name: Bot
# {
#	"state": {
#		"reported":{
#			"property":<R,G,Y>
#		}
#	}
#}

# Custom Shadow callback for updating the reported state in shadow
def customShadowCallback_Update(payload, responseStatus, token):
    # payload is a JSON string ready to be parsed using json.loads(...)
    # in both Py2.x and Py3.x
    if responseStatus == "timeout":
        print("Update request " + token + " time out!")
    if responseStatus == "accepted":
        payloadDict = json.loads(payload)
        print("~~~~~~~~~~ Shadow Update Accepted ~~~~~~~~~~~~~")
        print("Update request with token: " + token + " accepted!")
        print("humedad: " + str(payloadDict["state"]["reported"]["data"]["humedad"]))
        print("temperatura: " + str(payloadDict["state"]["reported"]["data"]["temperatura"]))
        print("~~~~~~~~~~~~~~~~~~~~~~~\n\n")
        
        persistir_datos()
    if responseStatus == "rejected":
        print("Update request " + token + " rejected!")


# Custom Shadow callback for retrieving the delta from the shadow
# A delta message is triggered by the switch GGAD updating the desired state
# This function then updates the reported state in the shadow - after changing the temp
def customShadowCallback_Delta(payload, responseStatus, token):
	# payload is a JSON string ready to be parsed using json.loads(...)
	# in both Py2.x and Py3.x
    global timestamp
    global temp
    global humedad
    payloadDict = json.loads(payload)
    print("++++++++ Received Shadow Delta ++++++++++")
    print(payloadDict)
    print("state: " + str(payloadDict["state"]))
    print("version: " + str(payloadDict["version"]))
    print("+++++++++++++++++++++++\n\n")
    try:
        humedad=payloadDict["state"]["data"]["humedad"]
        timestamp = payloadDict["metadata"]["data"]["humedad"]["timestamp"]
        print('Humedad encontrada en payload')
    except Exception:
        print("Humedad tiene el mismo valor.")
    try:
        temp=payloadDict["state"]["data"]["temperatura"]
        timestamp = payloadDict["metadata"]["data"]["temperatura"]["timestamp"]
        print('Temperatura encontrada en payload')
    except Exception:
        print("Temperatura tiene el mismo valor.")   
    JSONPayload = '{"state": {"reported": {"data": {"humedad": ' + '"' + humedad + '", "temperatura": ' + '"' + temp + '"}}}}'
    print("+++++++++++++++++++++++\n\n")
    print(JSONPayload)
    deviceShadowHandler.shadowUpdate(JSONPayload, customShadowCallback_Update, 5)


# function does basic regex check to see if value might be an ip address
def isIpAddress(value):
    match = re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}', value)
    if match:
        return True
    return False

# function reads host GGC ip address from filePath
def getGGCAddr(filePath):
    f = open(filePath, "r")
    return f.readline()

# Used to discover GGC group CA and end point. After discovering it persists in GROUP_PATH
def discoverGGC(host, iotCAPath, certificatePath, privateKeyPath, clientId):
    # Progressive back off core
    backOffCore = ProgressiveBackOffCore()

    # Discover GGCs
    discoveryInfoProvider = DiscoveryInfoProvider()
    discoveryInfoProvider.configureEndpoint(host)
    discoveryInfoProvider.configureCredentials(iotCAPath, certificatePath, privateKeyPath)
    discoveryInfoProvider.configureTimeout(10)  # 10 sec
    print("Iot end point: " + host)
    print("Iot CA Path: " + iotCAPath)
    print("GGAD cert path: " + certificatePath)
    print("GGAD private key path: " + privateKeyPath)
    print("GGAD thing name : " + clientId)
    retryCount = MAX_DISCOVERY_RETRIES
    discovered = False
    groupCA = None
    coreInfo = None
    while retryCount != 0:
        try:
            discoveryInfo = discoveryInfoProvider.discover(clientId)
            caList = discoveryInfo.getAllCas()
            coreList = discoveryInfo.getAllCores()

            # In this example we only have one core
            # So we pick the first ca and core info
            groupId, ca = caList[0]
            coreInfo = coreList[0]
            print("Discovered GGC: " + coreInfo.coreThingArn + " from Group: " + groupId)
            hostAddr = ""

            # In this example Ip detector lambda is turned on which reports
            # the GGC hostAddr to the CIS (Connectivity Information Service) that stores the
            # connectivity information for the AWS Greengrass core associated with your group.
            # This is the information used by discovery and the list of host addresses
            # could be outdated or wrong and you would normally want to
            # validate it in a better way.
            # For simplicity, we will assume the first host address that looks like an ip
            # is the right one to connect to GGC.
            # Note: this can also be set manually via the update-connectivity-info CLI
            for addr in coreInfo.connectivityInfoList:
                hostAddr = addr.host
                if isIpAddress(hostAddr):
                    break

            print("Discovered GGC Host Address: " + hostAddr)

            print("Now we persist the connectivity/identity information...")
            groupCA = GROUP_PATH + CA_NAME
            ggcHostPath = GROUP_PATH + GGC_ADDR_NAME
            if not os.path.exists(GROUP_PATH):
                os.makedirs(GROUP_PATH)
            groupCAFile = open(groupCA, "w")
            groupCAFile.write(ca)
            groupCAFile.close()
            groupHostFile = open(ggcHostPath, "w")
            groupHostFile.write(hostAddr)
            groupHostFile.close()

            discovered = True
            print("Now proceed to the connecting flow...")
            break
        except DiscoveryInvalidRequestException as e:
            print("Invalid discovery request detected!")
            print("Type: " + str(type(e)))
            print("Error message: " + e.message)
            print("Stopping...")
            break
        except BaseException as e:
            print("Error in discovery!")
            print("Type: " + str(type(e)))
            print("Error message: " + e.message)
            retryCount -= 1
            print("\n"+str(retryCount) + "/" + str(MAX_DISCOVERY_RETRIES) + " retries left\n")
            print("Backing off...\n")
            backOffCore.backOff()

    if not discovered:
        print("Discovery failed after " + str(MAX_DISCOVERY_RETRIES) + " retries. Exiting...\n")
        sys.exit(-1)

def persistir_datos():
    archivo = open('datos.txt', "w")
    archivo.write(str(humedad))
    archivo.write(",")
    archivo.write(str(temp))
    archivo.write(",")
    archivo.write(str(timestamp))
    archivo.write("\n")
    archivo.close()
    Data[0]=temp
    Data[1]=humedad
    Data[2]=timestamp
    schemadb.add_data(Data)

def cargar_datos():
    global temp,humedad,timestamp
    archivo = open('datos.txt', "r")
    print('-------------------------------------------------------------------------------------')
    humedad,temp,timestamp = archivo.readline().rstrip("\n").split(",")
    archivo.close()


iotCAPath ="root-ca-cert.pem"
host="a4f470uvj4nft-ats.iot.us-east-2.amazonaws.com" #Your AWS IoT custom endpoint
thingName = "GG_Rpi"
clientId = "GG_Subscriber"
privateKeyPath="3af6bd8ef5.private.key"
certificatePath="3af6bd8ef5.cert.pem"

# Configure logging
logger = logging.getLogger("AWSIoTPythonSDK.core")
logger.setLevel(logging.INFO) # set to logging.DEBUG for additional logging
streamHandler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
streamHandler.setFormatter(formatter)
logger.addHandler(streamHandler)

# Run Discovery service to check which GGC to connect to, if it hasn't been run already
# Discovery talks with the IoT cloud to get the GGC CA cert and ip address

if not os.path.isfile('./groupCA/root-ca.crt'):
    discoverGGC(host, iotCAPath, certificatePath, privateKeyPath, clientId)
else:
    print("Greengrass core has already been discovered.")

# read GGC Host Address from file
ggcAddrPath = GROUP_PATH + GGC_ADDR_NAME
rootCAPath = GROUP_PATH + CA_NAME
ggcAddr = getGGCAddr(ggcAddrPath)
print("GGC Host Address: " + ggcAddr)
print("GGC Group CA Path: " + rootCAPath)
print("Private Key of traffictemp thing Path: " + privateKeyPath)
print("Certificate of traffictemp thing Path: " + certificatePath)
print("Client ID(thing name for traffictemp): " + clientId)
print("Target shadow thing ID(thing name for traffictemp): " + thingName)

# Init AWSIoTMQTTShadowClient
myAWSIoTMQTTShadowClient = AWSIoTMQTTShadowClient(clientId)
myAWSIoTMQTTShadowClient.configureEndpoint(ggcAddr, 8883)
myAWSIoTMQTTShadowClient.configureCredentials(rootCAPath, privateKeyPath, certificatePath)

# AWSIoTMQTTShadowClient configuration
MQTTClient = myAWSIoTMQTTShadowClient.getMQTTConnection()
MQTTClient.configureOfflinePublishQueueing(-1)
myAWSIoTMQTTShadowClient.configureAutoReconnectBackoffTime(1, 32, 20)
myAWSIoTMQTTShadowClient.configureConnectDisconnectTimeout(10)  # 10 sec
myAWSIoTMQTTShadowClient.configureMQTTOperationTimeout(5)  # 5 sec

# Connect to AWS IoT
myAWSIoTMQTTShadowClient.connect()

# Create a deviceShadow with persistent subscription
deviceShadowHandler = myAWSIoTMQTTShadowClient.createShadowHandlerWithName(thingName, True)

# Listen on deltas - customShadowCallback_Delta will be called when a shadow delta message is received
deviceShadowHandler.shadowRegisterDeltaCallback(customShadowCallback_Delta)


cargar_datos()
Data[3] = {0,0,0}
tiempo = 3600 # Una hora atras

@app.route("/")
def main():
    tiempo = 3600 # Una hora atras
    return render_template('home.html',temp=temp,timestamp=timestamp)

@app.route("/_get_data", methods=['GET'])
def getData():
    return jsonify({'temperatura' : temp, 'humedad': humedad, 'timestamp' : str(timestamp)})


@app.route('/history')
def hist():
    global tiempo
    ts = time.time()
    ts = int(ts)
    ts2 = ts - tiempo
    #leo el historial de la bd 
    x = schemadb.busc_tiempo(ts2)
    N = x.count()
    print(x)
    date = []
    temp = []
    hum = []
    print(N)
    print("llega")
    if(N == 0):
        print("No hay resultados.")
        return render_template('history.html', date=date, temp=temp, hum=hum, cant=0)
    else:
        for item in x:
            date.append(item["Date"]) #agrego valores ya que date[0] no existe al crearlo vacio
            temp.append(item["Temp"])
            hum.append(item["Hum"]) 
        return render_template('history.html', date=date, temp=temp, hum=hum, cant=N)


@app.route('/history_dat', methods= ['POST'])
def get_d():
    global tiempo
    ts = time.time()
    ts = int(ts)
    ts2 = ts - tiempo
    #leo el historial de la bd 
    x = schemadb.busc_tiempo(ts2)
    N = x.count()
    print(x)
    date = []
    temp = []
    hum = []
    print(N)
    print("llega")
    if(N == 0):
        print("No hay resultados.")
        return jsonify({'date' : 0, 'hum': 0, 'temp' : 0, 'cant': N})
    else:
        for item in x:
            date.append(item["Date"]) #agrego valores ya que date[0] no existe al crearlo vacio
            temp.append(item["Temp"])
            hum.append(item["Hum"]) 
        return jsonify({'date' : date, 'hum': hum, 'temp' : temp, 'cant': N})


@app.route('/history_sel', methods=['POST'])
def handle_intervalo():
    inter = request.values.get('selected')
    print(inter)
    print ("Intervalo: " + inter)
    global tiempo
    if(inter == "H"):
        tiempo = 3600 #Una hora atras.
    if(inter == "D"):
        tiempo = 86400 #Un dia atras.
    if(inter == "W"):
        tiempo = 604800 #Una semana atras.
    if(inter == "Y"):
        tiempo = (86400*365) #Un año atras.
    print(tiempo)
    get_d()


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)

while True:
	time.sleep(1)
    

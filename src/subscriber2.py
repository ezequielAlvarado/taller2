#
# Copyright 2010-2017 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#



from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTShadowClient
import sys
import uuid
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
from flask import Flask
from flask import render_template
from flask_socketio import SocketIO

app = Flask(__name__)       
socketio = SocketIO(app)


MAX_DISCOVERY_RETRIES = 10    # MAX tries at discovery before giving up
GROUP_PATH = "./groupCA/"     # directory storing discovery info
CA_NAME = "root-ca.crt"       # stores GGC CA cert
GGC_ADDR_NAME = "ggc-host"    # stores GGC host address
temp="33"
timestamp="Que es esto"
datos = ['1','2']
coreInfo = any
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
        print("property: " + str(payloadDict["state"]["reported"]["property"]))
        print("~~~~~~~~~~~~~~~~~~~~~~~\n\n")
        datos[0]=temp
        datos[1]=timestamp
        socketio.emit('evento', datos )
    if responseStatus == "rejected":
        print("Update request " + token + " rejected!")


# Custom Shadow callback for retrieving the delta from the shadow
# A delta message is triggered by the switch GGAD updating the desired state
# This function then updates the reported state in the shadow - after changing the temp
def customShadowCallback_Delta(payload, responseStatus, token):
	# payload is a JSON string ready to be parsed using json.loads(...)
	# in both Py2.x and Py3.x
	payloadDict = json.loads(payload)
	print("++++++++ Received Shadow Delta ++++++++++")
	print(payloadDict)
	print("property: " + str(payloadDict["state"]["property"]))
	print("version: " + str(payloadDict["version"]))
	print("+++++++++++++++++++++++\n\n")
	global timestamp
	global temp
	temp = payloadDict["state"]["property"]
	timestamp = payloadDict["metadata"]["property"]["timestamp"]
	print("Temperatura cambiada: " + temp)
	JSONPayload = '{"state":{"reported":{"property":' + '"' + temp + '"}}}'
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


"""
# Read in command-line parameters
parser = argparse.ArgumentParser()
parser.add_argument("-e", "--endpoint", action="store", required=True, dest="host", help="Your AWS IoT custom endpoint")
parser.add_argument("-r", "--rootCA", action="store", required=True, dest="rootCAPath", help="Root CA file path")
parser.add_argument("-c", "--cert", action="store", dest="certificatePath", help="Certificate file path")
parser.add_argument("-k", "--key", action="store", dest="privateKeyPath", help="Private key file path")
parser.add_argument("-n", "--thingName", action="store", dest="thingName", default="Bot", help="Targeted thing name")
parser.add_argument("-id", "--clientId", action="store", dest="clientId", default="traffictemp",
                    help="Targeted client id")

args = parser.parse_args()
host = args.host
iotCAPath = args.rootCAPath
certificatePath = args.certificatePath
privateKeyPath = args.privateKeyPath
thingName = args.thingName
clientId = args.clientId
"""

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

    rootCAPath = GROUP_PATH + CA_NAME
    print("GGC Group CA Path: " + rootCAPath)
    print("Private Key thing Path: " + privateKeyPath)
    print("Certificate thing Path: " + certificatePath)
    print("Client ID(thing name): " + clientId)
    print("Target shadow thing ID(thing name of shadow): " + thingName)

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
            """
            connected=False
            for connectivityInfo in coreInfo.connectivityInfoList:
                currentHost = connectivityInfo.host
                currentPort = connectivityInfo.port
                print("Trying to connect to core at %s:%d" % (currentHost, currentPort))
                myAWSIoTMQTTShadowClient.configureEndpoint(currentHost, currentPort)
                try:
                    myAWSIoTMQTTShadowClient.connect()
                    connected = True
                    break
                except BaseException as e:
                    print("Error in connect!")
                    print("Type: %s" % str(type(e)))
                    print("Error message: %s" % e)

            if not connected:
                print("Cannot connect to core %s. Exiting..." % coreInfo.coreThingArn)
                sys.exit(-2)
            print("SE conecto!")
            """

            """print("Discovered GGC Host Address: " + hostAddr)"""


            print("Now we persist the connectivity/identity information...")
            groupCA = GROUP_PATH + groupId + "_CA_" + str(uuid.uuid4()) + ".crt"
            if not os.path.exists(GROUP_PATH):
                os.makedirs(GROUP_PATH)
            groupCAFile = open(groupCA, "w")
            groupCAFile.write(ca)
            groupCAFile.close()

            discovered = True
            print("Now proceed to the connecting flow...")
            break
            """
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
            """
        except DiscoveryInvalidRequestException as e:
            print("Invalid discovery request detected!")
            print("Type: " + str(type(e)))
            print("Error message: " + e.message)
            print("Stopping...")
            break
        except BaseException as e:
            print("Error in discovery!")
            print("Type: " + str(type(e)))
            print("Error message: " + e)
            retryCount -= 1
            print("\n"+str(retryCount) + "/" + str(MAX_DISCOVERY_RETRIES) + " retries left\n")
            print("Backing off...\n")
            backOffCore.backOff()
    if not discovered:
        print("Discovery failed after " + str(MAX_DISCOVERY_RETRIES) + " retries. Exiting...\n")
        sys.exit(-1)


    # Init AWSIoTMQTTShadowClient
    myAWSIoTMQTTShadowClient = AWSIoTMQTTShadowClient(clientId)
    myAWSIoTMQTTShadowClient.configureCredentials(groupCA, privateKeyPath, certificatePath)

    connected = False
    for connectivityInfo in coreInfo.connectivityInfoList:
        currentHost = connectivityInfo.host
        currentPort = connectivityInfo.port
        print("Trying to connect to core at %s:%d" % (currentHost, currentPort))
        myAWSIoTMQTTShadowClient.configureEndpoint(currentHost, currentPort)
        try:
            myAWSIoTMQTTShadowClient.connect()
            connected = True
            break
        except Exception as e:
            print("Error in connect!")
            print("Type: %s" % str(type(e)))
            print("Error message: %s" % e)

    if not connected:
        print("Cannot connect to core %s. Exiting..." % coreInfo.coreThingArn)
        sys.exit(-2)
else:
    print("Greengrass core has already been discovered.")





# AWSIoTMQTTShadowClient configuration
myAWSIoTMQTTShadowClient.configureAutoReconnectBackoffTime(1, 32, 20)
myAWSIoTMQTTShadowClient.configureConnectDisconnectTimeout(10)  # 10 sec
myAWSIoTMQTTShadowClient.configureMQTTOperationTimeout(5)  # 5 sec

# Connect to AWS IoT


# Create a deviceShadow with persistent subscription
deviceShadowHandler = myAWSIoTMQTTShadowClient.createShadowHandlerWithName(thingName, True)

# Listen on deltas - customShadowCallback_Delta will be called when a shadow delta message is received
deviceShadowHandler.shadowRegisterDeltaCallback(customShadowCallback_Delta)

@app.route("/")
def main():
    return render_template('home.html',temp=temp,timestamp=timestamp)

@app.route('/history')
def hist():
    return render_template('history.html')
    
    
def background_thread():
    """Example of how to send server generated events to clients."""
    while True:
        socketio.sleep(4)
        datos[0]=temp
        datos[1]=timestamp
        socketio.emit('evento', temp )
    
if __name__ == "__main__":
    socketio.run(app,debug=True)

while True:
	time.sleep(5)
    
"""

	
	print("Temperatura recibida: " + temp)
	print(timestamp)"""

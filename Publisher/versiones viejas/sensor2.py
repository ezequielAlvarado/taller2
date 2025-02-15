#
# Copyright 2010-2017 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# This Greengrass example simulates a traffic light (using a switch and light) cycling between G, Y, R by updating the desired property in the shadow. 
# Please refer to the AWS Greengrass Getting Started Guide, Module 5 for more information.
#
# This file is meant to be used in conjunction with trafficLight.py

from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTShadowClient
import sys
import logging
import time
import json
import argparse
import os
import re
from itertools import cycle

from AWSIoTPythonSDK.core.greengrass.discovery.providers import DiscoveryInfoProvider
from AWSIoTPythonSDK.core.protocol.connection.cores import ProgressiveBackOffCore
from AWSIoTPythonSDK.exception.AWSIoTExceptions import DiscoveryInvalidRequestException

MAX_DISCOVERY_RETRIES = 10    # MAX tries at discovery before giving up
GROUP_PATH = "./groupCA/"     # directory storing discovery info
CA_NAME = "root-ca.crt"       # stores GGC CA cert
GGC_ADDR_NAME = "ggc-host"    # stores GGC host address

# Shadow JSON schema:
#
# Name: Bot
# {
#	"state": {
#		"desired":{
#			"property":<R,G,Y>
#		}
#	}
# }

# Custom Shadow callback for updating the desired state in the shadow
def customShadowCallback_Update(payload, responseStatus, token):
    # payload is a JSON string ready to be parsed using json.loads(...)
    # in both Py2.x and Py3.x
    if responseStatus == "timeout":
        print("Update request " + token + " time out!")
    if responseStatus == "accepted":
        payloadDict = json.loads(payload)
        print("~~~~~~~~~~Shadow Update Accepted~~~~~~~~~~~~~")
        print("Update request with token: " + token + " accepted!")
        print("temperatura: " + str(payloadDict["state"]["desired"]["temperatura"]))
        print("presion: " + str(payloadDict["state"]["desired"]["presion"]))
        print("~~~~~~~~~~~~~~~~~~~~~~~\n\n")
        
    if responseStatus == "rejected":
        print("Update request " + token + " rejected!")

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

            # In this example we have one core
            # So we only pick the first ca and core info
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


iotCAPath ="root-ca-cert.pem"
host="a4f470uvj4nft-ats.iot.us-east-2.amazonaws.com" #Your AWS IoT custom endpoint
thingName = "GG_Rpi"
clientId = "GG_Sensor"
privateKeyPath="b49359523d.private.key"
certificatePath="b49359523d.cert.pem"


# Configure logging
logger = logging.getLogger("AWSIoTPythonSDK.core")
logger.setLevel(logging.INFO)   # set to logging.DEBUG for additional logging
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
print("Private Key of lightController thing Path: " + privateKeyPath)
print("Certificate of lightController thing Path: " + certificatePath)
print("Client ID(thing name for lightController): " + clientId)
print("Target shadow thing ID(thing name for trafficLight): " + thingName)

# Init AWSIoTMQTTShadowClient
myAWSIoTMQTTShadowClient = AWSIoTMQTTShadowClient(clientId)
myAWSIoTMQTTShadowClient.configureEndpoint(ggcAddr, 8883)
myAWSIoTMQTTShadowClient.configureCredentials(rootCAPath, privateKeyPath, certificatePath)

# AWSIoTMQTTShadowClient configuration
myAWSIoTMQTTShadowClient.configureAutoReconnectBackoffTime(1, 32, 20)
myAWSIoTMQTTShadowClient.configureConnectDisconnectTimeout(10)  # 10 sec
myAWSIoTMQTTShadowClient.configureMQTTOperationTimeout(5)  # 5 sec

# Connect to AWS IoT
myAWSIoTMQTTShadowClient.connect()

# Create a deviceShadow with persistent subscription
deviceShadowHandler = myAWSIoTMQTTShadowClient.createShadowHandlerWithName(thingName, True)

# This loop simulates a traffic light cycling between G, Y, R by updating the desired property in the shadow
# This uses the desired property because the light GGAD will get the request for changing and update the reported property
# The idea is the desired property is a request to update the light while the reported property is the actual value of the light
states = ['22','24','26','30','29','28','27','25','20','23']
pool = cycle(states) 
for item in pool: 
    JSONPayload = '{"state":{"desired":{"temperatura":' + '"' + item + '", "presion":' + '"' + item + '"}}}'
    print(JSONPayload)
    deviceShadowHandler.shadowUpdate(JSONPayload, customShadowCallback_Update, 5)
    time.sleep(10)

# https://techtutorialsx.com/2017/04/23/python-subscribing-to-mqtt-topic/

import getpass 
import paho.mqtt.client as mqttClient
import time
import matplotlib.pyplot as plt
import matplotlib.animation as anim
import matplotlib.style as style
import numpy as np
import csv
from datetime import datetime
import os
import platform
import logging
import argparse
 
# MQTT related variables
gMqttClient = ""
gMqttBrokerAddr= "192.168.1.2"
gMqttBrokerPort = 1883
gMqttUser = "emonpi"
gMqttPswd = ""
gMqttConnected = False #global variable for the state of the connection
gMqttErrorCounter = 0

# Log related
MAX_LOG_SIZE = 1000000
gLogCsvColumns = ['date','time','HCHC','HCHP','PTEC','IINST','PAPP','ErrorCounter']
gLogCsvFile = ""
gLogCsvFileIdx=0
gLogCsvDictData={
    "date":"",
    "time":"",
    "HCHC": 0,
    "HCHP": 0,
    "PTEC": 0,
    "IINST": 0,
    "PAPP": 0,
    "ErrorCounter": 0
}
gLogDay=""

# Graph related variables
style.use('fast')
fig = plt.figure()
ax1 = fig.add_subplot(1,1,1)
ys = []
allow_graph=0

####################
# callback from mqtt client
def on_connect(client, userdata, flags, rc):
    global gMqttConnected
    if rc == 0:
        logging.info("Connected to broker")
        gMqttConnected = True                #Signal connection 
        #client.subscribe("AntoineHome/TIC/IINST")
        client.subscribe("AntoineHome/TIC/#")
    else:
        logging.info("Connection failed")

def on_disconnect(client, userdata, flags, rc):
    global gMqttConnected
    logging.info("Connection to broker lost")
    gMqttConnected = False

####################
# callback from mqtt client
def on_message(client, userdata, msg):
    logging.info("Message received from " + msg.topic + ":" + str(msg.payload))
    if msg.topic == "AntoineHome/TIC/HCHC":
        gLogCsvDictData["HCHC"]=int(msg.payload)
    elif msg.topic == "AntoineHome/TIC/HCHP":
        gLogCsvDictData["HCHP"]=int(msg.payload)
    elif msg.topic == "AntoineHome/TIC/PTEC":
        gLogCsvDictData["PTEC"]=int(msg.payload)
    elif msg.topic == "AntoineHome/TIC/IINST":
        gLogCsvDictData["IINST"]=int(msg.payload)
        ys.append(int(msg.payload))
        if len(ys) > 100:
            ys.remove(ys[0])
    elif msg.topic == "AntoineHome/TIC/PAPP":
        gLogCsvDictData["PAPP"]=int(msg.payload)
        #save to csv file only when last topic is received
        # PAPP is the last topic refreshed by the publisher
        save_to_csv()

####################
# save received data in a csv file
def save_to_csv():
    global gMqttErrorCounter
    global gLogCsvFileIdx
    global gLogDay

    #after midnight create a new log file
    now = datetime.now()
    current_day = now.strftime("%d")
    if current_day != gLogDay:
        #reset file idx and create new log file
        gLogCsvFileIdx = 0
        configure_csv(gLogCsvFileIdx)

    # don't save in csv file if data is 0 (probably due do TIC info not valid)
    if gLogCsvDictData["HCHC"] != 0 and gLogCsvDictData["PAPP"] != 0:
        size = os.stat(gLogCsvFile).st_size
        #print("log size="+ str(size))
        if size > MAX_LOG_SIZE:
            gLogCsvFileIdx+=1
            configure_csv(gLogCsvFileIdx)
        
        gLogCsvDictData["date"]=now.strftime("%Y/%m/%d")
        gLogCsvDictData["time"]=now.strftime("%H:%M:%S")
        #print("csv_file="+ csv_file)
        try:
            with open(gLogCsvFile, 'a') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=gLogCsvColumns, delimiter=',', lineterminator='\n')
                writer.writerow(gLogCsvDictData)
        except IOError:
            logging.error("I/O error")
    else:
        gMqttErrorCounter += 1
        gLogCsvDictData["ErrorCounter"] = gMqttErrorCounter
        logging.error("Data to save are not valid")


####################
# create csv file and write header
def configure_csv(idx):
    global gLogCsvFile
    global gLogDay
    logging.info("Current folder:"+os.getcwd())
    now = datetime.now()
    gLogDay = now.strftime("%d")
    gLogCsvFile = "TIC_log_"+now.strftime("%Y%m%d")+"_"+str(idx)+".csv"
    logging.info("#configure_csv: "+gLogCsvFile)
    try:
       with open(gLogCsvFile, 'w') as csvfile: 
            writer = csv.DictWriter(csvfile, fieldnames=gLogCsvColumns, delimiter=',', lineterminator='\r')
            writer.writeheader()
    except IOError:
        logging.error("I/O error")

####################
# request a password to use for MQTT connection
def login():
    _user = getpass.getuser() 
    if _user != "":
        user = _user
    #else use default user name
    password = getpass.getpass()

####################
# initialize matplot graph
def init_graph():
    #don't use matplot graph if the script is running on the raspberry pi
    if platform.uname()[1] != "raspberrypi" and allow_graph==1:
        ani = anim.FuncAnimation(fig, update_graph, interval=1000, repeat=True)
        plt.show()
        ax1.set_ylabel('IINST')
        #ax1.set_xlim(0, 20)
        #ax1.set_ylim(0, 20)

####################
# add data to graph and redraw
def update_graph(i):
    if platform.uname()[1] != "raspberrypi" and allow_graph==1:
        ax1.clear()
        ax1.plot(ys)

####################
# handle arguments passed to the script
def handle_main_arg():
    global allow_graph
    parser = argparse.ArgumentParser()
    parser.add_argument("-v","--verbose", help="enable verbosity mode ", action="store_true")
    parser.add_argument("-g","--graphic", help="trace IINST in graphic view", action="store_true")
    args = parser.parse_args()
    if args.verbose:
        logging.basicConfig(level=logging.INFO)
    else:
        logging.basicConfig(level=logging.CRITICAL)
    if args.graphic:
        allow_graph=1
    else:
        allow_graph = 0

####################
# configure MQTT client and open connection
def init_mqtt():
    global gMqttClient
    #user platform name as client so multiple device can run the same script
    gMqttClient = mqttClient.Client(platform.uname()[1])               #create new instance
    gMqttClient.username_pw_set(gMqttUser, password=gMqttPswd)    #set username and password
    gMqttClient.on_connect= on_connect                      #attach function to callback
    gMqttClient.on_message= on_message                      #attach function to callback
    gMqttClient.on_socket_close= on_disconnect

    gMqttClient.reconnect_delay_set(min_delay=10)

    try:
        gMqttClient.connect(gMqttBrokerAddr, port=gMqttBrokerPort)  #connect to broker
        gMqttClient.loop_start()                        #start the loop
 
        while gMqttConnected != True:    #Wait for connection
            time.sleep(0.1)
        return True

    except ConnectionRefusedError:
        logging.info("Was not able to connect to MQTT broker")
        return False

####################
def main():
    global gMqttConnected
    global gMqttClient
    #login()
    configure_csv(gLogCsvFileIdx)
    while init_mqtt() == False:
        logging.info("init_mqtt fail")
    init_graph()
    try:
        while True:
            time.sleep(1)
                
    except KeyboardInterrupt:
        logging.info("exiting")
        gMqttClient.disconnect()
        gMqttClient.loop_stop()

####################
if __name__ == "__main__":
    handle_main_arg()
    main()
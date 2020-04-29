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
MqttClient = ""
broker_address= "192.168.1.2"
port = 1883
user = "emonpi"
password = ""
Connected = False #global variable for the state of the connection
ErrorCounter = 0

# Log related
MAX_LOG_SIZE = 1000000
csv_columns = ['datetime','HCHC','HCHP','PTEC','IINST','PAPP','ErrorCounter']
csv_file = ""
file_idx=0
dict_data={
    "datetime":"",
    "HCHC": 0,
    "HCHP": 0,
    "PTEC": 0,
    "IINST": 0,
    "PAPP": 0,
    "ErrorCounter": 0
}

# Graph related variables
style.use('fast')
fig = plt.figure()
ax1 = fig.add_subplot(1,1,1)
ys = []
allow_graph=0

####################
# callback from mqtt client
def on_connect(client, userdata, flags, rc):
    global Connected
    if rc == 0:
        logging.info("Connected to broker")
        Connected = True                #Signal connection 
        #client.subscribe("AntoineHome/TIC/IINST")
        client.subscribe("AntoineHome/TIC/#")
    else:
        logging.info("Connection failed")

def on_disconnect(client, userdata, flags, rc):
    global Connected
    logging.info("Connection to broker lost")
    Connected = False

####################
# callback from mqtt client
def on_message(client, userdata, msg):
    logging.info("Message received from " + msg.topic + ":" + str(msg.payload))
    if msg.topic == "AntoineHome/TIC/HCHC":
        dict_data["HCHC"]=int(msg.payload)
    elif msg.topic == "AntoineHome/TIC/HCHP":
        dict_data["HCHP"]=int(msg.payload)
    elif msg.topic == "AntoineHome/TIC/PTEC":
        dict_data["PTEC"]=int(msg.payload)
    elif msg.topic == "AntoineHome/TIC/IINST":
        dict_data["IINST"]=int(msg.payload)
        ys.append(int(msg.payload))
        if len(ys) > 100:
            ys.remove(ys[0])
    elif msg.topic == "AntoineHome/TIC/PAPP":
        dict_data["PAPP"]=int(msg.payload)
        #save to csv file only when last topic is received
        # PAPP is the last topic refreshed by the publisher
        save_to_csv()

####################
# save received data in a csv file
def save_to_csv():
    global ErrorCounter
    global file_idx
    # don't save in csv file if data is 0 
    # probably due do TIC info not valid
    if dict_data["HCHC"] != 0 and dict_data["PAPP"] != 0:
        size = os.stat(csv_file).st_size
        #print("log size="+ str(size))
        if size > MAX_LOG_SIZE:
            file_idx+=1
            configure_csv(file_idx)
        now = datetime.now()
        dict_data["datetime"]=now.strftime("%Y/%m/%d %H:%M:%S")
        #print("csv_file="+ csv_file)
        try:
            with open(csv_file, 'a') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=csv_columns, delimiter=',', lineterminator='\n')
                writer.writerow(dict_data)
        except IOError:
            logging.error("I/O error")
    else:
        ErrorCounter += 1
        dict_data["ErrorCounter"] = ErrorCounter
        logging.error("Data to save are not valid")


####################
# create csv file and write header
def configure_csv(idx):
    global csv_file
    logging.info("Current folder:"+os.getcwd())
    now = datetime.now()
    csv_file = "TIC_log_"+now.strftime("%Y%m%d")+"_"+str(idx)+".csv"
    logging.info("#configure_csv: "+csv_file)
    try:
       with open(csv_file, 'w') as csvfile: 
            writer = csv.DictWriter(csvfile, fieldnames=csv_columns, delimiter=',', lineterminator='\r')
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
    global MqttClient
    #user platform name as client so multiple device can run the same script
    MqttClient = mqttClient.Client(platform.uname()[1])               #create new instance
    MqttClient.username_pw_set(user, password=password)    #set username and password
    MqttClient.on_connect= on_connect                      #attach function to callback
    MqttClient.on_message= on_message                      #attach function to callback
    MqttClient.on_socket_close= on_disconnect

    MqttClient.reconnect_delay_set(min_delay=10)

    try:
        MqttClient.connect(broker_address, port=port)  #connect to broker
        MqttClient.loop_start()                        #start the loop
 
        while Connected != True:    #Wait for connection
            time.sleep(0.1)
        return True

    except ConnectionRefusedError:
        logging.info("Was not able to connect to MQTT broker")
        return False

####################
def main():
    global Connected
    global MqttClient
    #login()
    configure_csv(file_idx)
    while init_mqtt() == False:
        logging.info("init_mqtt fail")
    init_graph()
    try:
        while True:
            time.sleep(1)
                
    except KeyboardInterrupt:
        logging.info("exiting")
        MqttClient.disconnect()
        MqttClient.loop_stop()

####################
if __name__ == "__main__":
    handle_main_arg()
    main()
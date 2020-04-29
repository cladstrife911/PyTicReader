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
 
# MQTT related variables
broker_address= "192.168.1.2"
port = 1883
user = "emonpi"
password = ""
Connected = False #global variable for the state of the connection

# Log related
csv_columns = ['datetime','HCHC','HCHP','PTEC','IINST','PAPP']
csv_file = ""
file_idx=0
dict_data={
    "datetime":"",
    "HCHC": 0,
    "HCHP": 0,
    "PTEC": 0,
    "IINST":0,
    "PAPP":0
}

# Graph related variables
style.use('fast')
fig = plt.figure()
ax1 = fig.add_subplot(1,1,1)
ys = []

####################
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to broker")
        global Connected                #Use global variable
        Connected = True                #Signal connection 
    else:
        print("Connection failed")

####################
def on_message(client, userdata, msg):
    print("Message received from " + msg.topic + ":" + str(msg.payload))
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
        save_to_csv()

####################
def save_to_csv():
    global file_idx
    size = os.stat(csv_file).st_size
    #print("log size="+ str(size))
    if size > 10000:
        file_idx+=1
        configure_csv(file_idx)
    now = datetime.now()
    dict_data["datetime"]=now.strftime("%Y/%m/%d %H:%M:%S")
    #print("csv_file="+ csv_file)
    try:
        with open(csv_file, 'a') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=csv_columns, delimiter=',', lineterminator='\r')
            writer.writerow(dict_data)
    except IOError:
        print("I/O error")

####################
def configure_csv(idx):
    global csv_file
    now = datetime.now()
    csv_file = "TIC_log_"+now.strftime("%Y%m%d")+"_"+str(idx)+".csv"
    print("#configure_csv: "+csv_file)
    try:
       with open(csv_file, 'w') as csvfile: 
            writer = csv.DictWriter(csvfile, fieldnames=csv_columns, delimiter=',', lineterminator='\r')
            writer.writeheader()
    except IOError:
        print("I/O error")

####################
# request a password to use for MQTT connection
def login():
    _user = getpass.getuser() 
    if _user != "":
        user = _user
    #else use default user name
    password = getpass.getpass()

def init_graph():
    ax1.set_ylabel('IINST')
    #ax1.set_xlim(0, 20)
    #ax1.set_ylim(0, 20)

def update_graph(i):
    if platform.uname()[1] != "raspberrypi":
        ax1.clear()
        ax1.plot(ys)

####################
def main():
    #login()

    client = mqttClient.Client("Python")               #create new instance
    client.username_pw_set(user, password=password)    #set username and password
    client.on_connect= on_connect                      #attach function to callback
    client.on_message= on_message                      #attach function to callback

    client.connect(broker_address, port=port)  #connect to broker
    client.loop_start()                        #start the loop
 
    while Connected != True:    #Wait for connection
        time.sleep(0.1)
 
    configure_csv(file_idx)

    #client.subscribe("AntoineHome/TIC/IINST")
    client.subscribe("AntoineHome/TIC/#")

    #don't use matplot graph if the script is running on the raspberry pi
    if platform.uname()[1] != "raspberrypi":
        init_graph()
        ani = anim.FuncAnimation(fig, update_graph, interval=1000, repeat=True)
        plt.show()

    try:
        while True:
            time.sleep(1)
 
    except KeyboardInterrupt:
        print("exiting")
        client.disconnect()
        client.loop_stop()


####################
if __name__ == "__main__":
    main()
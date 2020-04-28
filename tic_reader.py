# https://techtutorialsx.com/2017/04/23/python-subscribing-to-mqtt-topic/

import getpass 
import paho.mqtt.client as mqttClient
import time
import matplotlib.pyplot as plt
import matplotlib.animation as anim
import matplotlib.style as style
import numpy as np

Connected = False #global variable for the state of the connection
 
broker_address= "192.168.1.2"
port = 1883
user = "emonpi"
password = ""

style.use('fast')

fig = plt.figure()
ax1 = fig.add_subplot(1,1,1)
xs = []
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
    if msg.topic == "AntoineHome/TIC/IINST":
        ys.append(int(msg.payload))
        if len(ys) > 100:
            ys.remove(ys[0])

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
    ax1.set_xlim(0, 20)
    ax1.set_ylim(0, 20)

def update_graph(i):
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
 
    #client.subscribe("AntoineHome/TIC/IINST")
    client.subscribe("AntoineHome/TIC/#")

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
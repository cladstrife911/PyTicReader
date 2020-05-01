#!/bin/bash

#Stop the current running service
sudo systemctl stop tic_reader.service

#get the latest version of the SW
git pull

#service file has change so need to reload
sudo systemctl daemon-reload

#Start the service again
sudo systemctl start tic_reader.service
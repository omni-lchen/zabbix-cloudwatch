#!/bin/bash

# Date:   08/08/2015
# Author: Long Chen
# Description: A script to bulk send ELB cloudwatch data to zabbix server

PATH=$PATH:/opt/zabbix/cloudwatch/
export PATH

# Client Id
CLIENT_ID=$1
# Client Id
DOMAIN_NAME=$2
# Zabbix Host
ZABBIX_HOST=$3
# Zabbix Server
ZABBIX_SERVER=$4
# AWS Account
ACCOUNT=$5
# AWS Region
REGION=$6
# Collecting 5-minute data from cloudwatch
PERIOD="300"
# Set start time and end time for collecting cloudwatch data
ENDTIME=$(date -u "+%F %H:%M:00" -d "5 minutes ago")
STARTTIME=$(date -u "+%F %H:%M:00" -d "10 minutes ago")

# Send cloudwatch data of a table to Zabbix Server
zabbixCloudWatch.py -z "$ZABBIX_SERVER" -x "$ZABBIX_HOST" -a "$ACCOUNT" -r "$REGION" -s "ES" -d "ClientId=$CLIENT_ID,DomainName=$DOMAIN_NAME" -p "$PERIOD" -f "$STARTTIME" -t "$ENDTIME"
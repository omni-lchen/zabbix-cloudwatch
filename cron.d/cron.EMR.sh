#!/bin/bash

PATH=$PATH:/opt/zabbix-cloudwatch
export PATH

# Load Balancer Name
EMR_CLUSTER_NAME=$1
# Zabbix Host
ZABBIX_HOST=$2
# Zabbix Server
ZABBIX_SERVER=$3
# AWS Account
ACCOUNT=$4
# AWS Region
REGION=$5
# Collecting 5-minute data from cloudwatch
PERIOD="300"
# Set start time and end time for collecting cloudwatch data
STARTTIME=$(date -u "+%F %H:%M:00" -d "5 minutes ago")
ENDTIME=$(date -u "+%F %H:%M:00")

# Send cloudwatch data of a table to Zabbix Server
zabbixCloudWatch.py -z "$ZABBIX_SERVER" -x "$ZABBIX_HOST" -a "$ACCOUNT" -r "$REGION" -s "ElasticMapReduce" -d "JobFlowId=$EMR_CLUSTER_NAME" -p "$PERIOD" -f "$STARTTIME" -t "$ENDTIME"
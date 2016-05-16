#!/bin/bash

# Date:   13/05/2016
# Author: Long Chen
# Description: A script to bulk send SQS cloudwatch data to zabbix server
# Requires jq command to parse json data
# JQ download link: http://stedolan.github.io/jq/download/

PATH=$PATH:/opt/zabbix/cloudwatch
export PATH

# Prefix component name used for SQS queues discovery
COMPONENT=$1
# Get SQS Main Queue or Dead Letter Queue
QUERY=$2
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
ENDTIME=$(date -u "+%F %H:%M:00")
STARTTIME=$(date -u "+%F %H:%M:00" -d "10 minutes ago")

# Search queues used for a component
if [ $QUERY = "SQSMainQueue" ]; then
  QUEUES=$(awsLLD.py -a "$ACCOUNT" -r "$REGION" -q "SQSMainQueue" -c "$COMPONENT" | jq '.data[]["{#MQNAME}"]' | xargs)
elif [ $QUERY = "SQSDeadLetterQueue" ]; then
  QUEUES=$(awsLLD.py -a "$ACCOUNT" -r "$REGION" -q "SQSDeadLetterQueue" -c "$COMPONENT" | jq '.data[]["{#DQNAME}"]' | xargs)
else
  echo "Wrong query."
fi

if [ -n "$QUEUES" ]; then
  for queue in $QUEUES
    do
      # Send cloudwatch data of a table to Zabbix Server
      zabbixCloudWatch.py -z "$ZABBIX_SERVER" -x "$ZABBIX_HOST" -a "$ACCOUNT" -r "$REGION" -s "SQS" -d "QueueName=$queue" -p "$PERIOD" -f "$STARTTIME" -t "$ENDTIME"
  done
fi
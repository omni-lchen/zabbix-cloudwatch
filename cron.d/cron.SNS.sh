#!/bin/bash

# Date:   09/11/2015
# Author: Long Chen
# Description: A script to bulk send SNS cloudwatch data to zabbix server
# Requires jq command to parse json data
# JQ download link: http://stedolan.github.io/jq/download/

PATH=$PATH:/opt/zabbix/cloudwatch
export PATH

# Prefix component name used for SNS topics discovery
COMPONENT=$1
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
# Adding lag, as CloudWatch doesn't send all data if requested too early.
ENDTIME=$(date -u "+%F %H:%M:00" -d "5 minutes ago")
STARTTIME=$(date -u "+%F %H:%M:00" -d "10 minutes ago")

# Search topics used for a component
TOPICS=$(awsLLD.py -a "$ACCOUNT" -r "$REGION" -q "SNSTopics" -c "$COMPONENT" | jq '.data[]["{#TOPIC_NAME}"]' | xargs)

if [ -n "$TOPICS" ]; then
  for topic in $TOPICS
    do
      # Send cloudwatch data of a table to Zabbix Server
      zabbixCloudWatch.py -z "$ZABBIX_SERVER" -x "$ZABBIX_HOST" -a "$ACCOUNT" -r "$REGION" -s "SNS" -d "TopicName=$topic" -p "$PERIOD" -f "$STARTTIME" -t "$ENDTIME"
  done
fi

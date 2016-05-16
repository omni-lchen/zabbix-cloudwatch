#!/bin/bash

# Date:   08/08/2015
# Author: Long Chen
# Description: A script to bulk send DynamoDB cloudwatch data to zabbix server
# Requires jq command to parse json data
# JQ download link: http://stedolan.github.io/jq/download/

PATH=$PATH:/opt/zabbix/cloudwatch
export PATH

# Prefix component name used for DynamoDB tables discovery
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
ENDTIME=$(date -u "+%F %H:%M:00")
STARTTIME=$(date -u "+%F %H:%M:00" -d "15 minutes ago")

# Search tables used for a component
TABLES=$(awsLLD.py -a "$ACCOUNT" -r "$REGION" -q "DynamoDBTables" -c "$COMPONENT" | jq '.data[]["{#TABLE_NAME}"]' | xargs)

if [ -n "$TABLES" ]; then
  for table in $TABLES
    do
    # Send cloudwatch data of a table to Zabbix Server
    zabbixCloudWatch.py -z "$ZABBIX_SERVER" -x "$ZABBIX_HOST" -a "$ACCOUNT" -r "$REGION" -s "DynamoDB" -d "TableName=$table" -p "$PERIOD" -f "$STARTTIME" -t "$ENDTIME"
  done
fi
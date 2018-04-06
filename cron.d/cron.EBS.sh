#!/bin/bash

# Date:   08/08/2015
# Author: Long Chen
# Description: A script to bulk send ELB cloudwatch data to zabbix server

PATH=$PATH:/opt/zabbix/cloudwatch
export PATH

# EBS Name
VOLUME_ID=$1
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

# Send cloudwatch data of a table to Zabbix Server
zabbixCloudWatch.py -z "$ZABBIX_SERVER" -x "$ZABBIX_HOST" -a "$ACCOUNT" -r "$REGION" -s "EBS" -d "VolumeId=$VOLUME_ID" -p "$PERIOD" -f "$STARTTIME" -t "$ENDTIME"

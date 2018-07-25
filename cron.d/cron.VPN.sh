#!/bin/bash

# Description: A script to bulk send VPN cloudwatch data to zabbix server

PATH=$PATH:/opt/zabbix/cloudwatch
export PATH

# VPN indentifier
VPNID=$1
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
STARTTIME=$(date -u "+%F %H:%M:00" -d "5 minutes ago")

# Send cloudwatch data of a table to Zabbix Server
zabbixCloudWatch.py -z "$ZABBIX_SERVER" -x "$ZABBIX_HOST" -a "$ACCOUNT" -r "$REGION" -s "VPN" -d "VpnId=$VPNID" -p "$PERIOD" -f "$STARTTIME" -t "$ENDTIME"

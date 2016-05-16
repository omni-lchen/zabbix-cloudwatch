#!/bin/sh

# Date:                 08/08/2015
# Author:               Long Chen
# Description:          AWS discovery bash wrapper used in zabbix discovery rule as external script

LLDCMD=/opt/zabbix/cloudwatch/awsLLD.py
ACCOUNT=$1
REGION=$2
QUERY=$3
COMPONENT=$4

# Execute the awsLLD command to get a list of dimensions for a component
# QUERY: SQSMainQueue, SQSDeadLetterQueue, DynamoDBTables, SNSTopics
$LLDCMD -a $ACCOUNT -r $REGION -q $QUERY -c $COMPONENT

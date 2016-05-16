#!/usr/bin/env python

# Date:   08/08/2015
# Author: Long Chen
# Description: A script to discover aws dimensions in a component  e.g. SQS queues, DynamoDB tables
# Example Usage: omniAWSLLD.py -a awscore -r us-east-1 -q DynamoDBTables -c catalogue-management-PROD

import re
import json
from optparse import OptionParser
from awsAccount import awsAccount
from awsConnection import awsConnection

def config_parser():
    parser = OptionParser(usage="usage: %prog [options]", version="%prog 1.0")
    parser.add_option("-a", "--account", dest="accountname", help="account name", metavar="ACCOUNT")
    parser.add_option("-r", "--region", dest="region", help="region", metavar="REGION")
    parser.add_option("-q", "--query", dest="query", help="specify a query", metavar="QUERY")
    parser.add_option("-c", "--component", dest="component", help="component name", metavar="COMPONENT")
    return parser

def getSQSMainQueueByComponent(a, r, c):
    account = a
    aws_account = awsAccount(account)
    aws_access_key_id = aws_account._aws_access_key_id
    aws_secret_access_key = aws_account._aws_secret_access_key
    aws_region = r
    component = c
    # Init LLD Data
    lldlist = []
    llddata = {"data":lldlist}
    # Connect to SQS
    conn = awsConnection()
    conn.sqsConnect(aws_region, aws_access_key_id, aws_secret_access_key)
    sqsConn = conn._aws_connection
    # Get a list all SQS queues
    queues = sqsConn.get_all_queues()

    # Save queue names in a list
    qdata = []
    for q in queues:
        qname = q.name
        # Filter out dead letter queues and only get the queues for a component in PROD
        if not re.search('dead', qname, re.I) and re.search(component, qname) and re.search('prod', qname, re.I):
            qdata.append(qname)

    # Add Zabbix LLD Macros into LLD data
    if qdata:
        for x in qdata:
            dict = {}
            # Get queue name
            dict["{#MQNAME}"] = x
            # Get short queue name by removing component name
            dict["{#MINAME}"] = re.sub(component + '(-?)', '', x)
            lldlist.append(dict)

    # Print LLD data in json format
    print json.dumps(llddata, indent=4)

def getSQSDeadLetterQueueByComponent(a, r, c):
    account = a
    aws_account = awsAccount(account)
    aws_access_key_id = aws_account._aws_access_key_id
    aws_secret_access_key = aws_account._aws_secret_access_key
    aws_region = r
    component = c
    # Init LLD Data
    lldlist = []
    llddata = {"data":lldlist}
    # Connect to SQS
    conn = awsConnection()
    conn.sqsConnect(aws_region, aws_access_key_id, aws_secret_access_key)
    sqsConn = conn._aws_connection

    # Get a list of all SQS queues
    queues = sqsConn.get_all_queues()

    # Save queue names in a list
    qdata = []
    for q in queues:
        qname = q.name
        # Search for DEAD letter queue in PROD
        if re.search('dead', qname, re.I) and re.search(component, qname) and re.search('prod', qname, re.I):
            qdata.append(qname)
    
    # Add Zabbix LLD Macros into LLD data
    if qdata:
        for x in qdata:
            dict = {}
            # Get queue name
            dict["{#DQNAME}"] = x
            # Get short queue name by removing component name
            dict["{#DINAME}"] = re.sub(component + '(-?)', '', x)
            lldlist.append(dict)

    # Print LLD data in json format
    print json.dumps(llddata, indent=4)

def getDynamoDBTables(a, r, c):
    account = a
    aws_account = awsAccount(account)
    aws_access_key_id = aws_account._aws_access_key_id
    aws_secret_access_key = aws_account._aws_secret_access_key
    aws_region = r
    component = c
    # Init LLD Data
    lldlist = []
    llddata = {"data":lldlist}
    # Connect to DynamoDB service
    conn = awsConnection()
    conn.dynamodbConnect(aws_region, aws_access_key_id, aws_secret_access_key)
    dynamoDBConn = conn._aws_connection
    # Get a list of DynamoDB tables
    tables = dynamoDBConn.layer1.list_tables()

    # Save table names in a list
    tdata = []
    for tname in tables['TableNames']:
        # Filter out table names and only get the DynamoDB tables for a component in PROD
        if re.search(component, tname) and not re.search('test', tname, re.I):
            tdata.append(tname)

    # Add Zabbix LLD Macros into LLD data
    if tdata:
        for x in tdata:
            dict = {}
            # Get aws account
            dict["{#AWS_ACCOUNT}"] = a
            # Get aws region
            dict["{#AWS_REGION}"] = r
            # Get table name
            dict["{#TABLE_NAME}"] = x
            lldlist.append(dict)

    # Print LLD data in json format
    print json.dumps(llddata, indent=4)

def getSNSTopics(a, r, c):
    account = a
    aws_account = awsAccount(account)
    aws_access_key_id = aws_account._aws_access_key_id
    aws_secret_access_key = aws_account._aws_secret_access_key
    aws_region = r
    component = c
    # Init LLD Data
    lldlist = []
    llddata = {"data":lldlist}
    # Connect to DynamoDB service
    conn = awsConnection()
    conn.snsConnect(aws_region, aws_access_key_id, aws_secret_access_key)
    snsConn = conn._aws_connection

    # Save SNS topics results in a list
    topicsResultsList = []
    # Save topic names in a list
    tdata = []

    # Get a list of SNS Topics
    topicsResults = snsConn.get_all_topics()
    topicsResultsList.append(topicsResults)
    # Get next token from current results, which will be used to get the next one
    nextToken = topicsResults['ListTopicsResponse']['ListTopicsResult']['NextToken']
    # If next token is not empty, get the next topic list
    while nextToken:
        topicsResults = snsConn.get_all_topics(nextToken)
        topicsResultsList.append(topicsResults)
        nextToken = topicsResults['ListTopicsResponse']['ListTopicsResult']['NextToken']

    for tr in topicsResultsList:
        for t in tr['ListTopicsResponse']['ListTopicsResult']['Topics']:
            topicArn = t['TopicArn']
            # Remove prefix string "arn:aws:sns:<aws region>:<random number>:" from topic arn
            topicName = re.sub('^arn:aws:sns:' + r + ':[0-9]+:', '', topicArn)
            # Filter out topic names and only get the topic names for a component in PROD
            if re.search(component, topicName) and re.search('prod', topicName, re.I):
                tdata.append(topicName)

    # Add Zabbix LLD Macros into LLD data
    if tdata:
        for x in tdata:
            dict = {}
            # Get aws account
            dict["{#AWS_ACCOUNT}"] = a
            # Get aws region
            dict["{#AWS_REGION}"] = r
            # Get topic name
            dict["{#TOPIC_NAME}"] = x
            # Get short topic name by removing component name
            dict["{#TOPIC_INAME}"] = re.sub(component + '(-?)', '', x)
            lldlist.append(dict)

    # Print LLD data in json format
    print json.dumps(llddata, indent=4)

if __name__ == '__main__':
    parser = config_parser()
    (options, args) = parser.parse_args()

    account = options.accountname
    region = options.region
    query = options.query
    component = options.component

    if query == 'SQSMainQueue':
        getSQSMainQueueByComponent(account, region, component)
    elif query == 'SQSDeadLetterQueue':
        getSQSDeadLetterQueueByComponent(account, region, component)
    elif query == 'DynamoDBTables':
        getDynamoDBTables(account, region, component)
    elif query == 'SNSTopics':
        getSNSTopics(account, region, component)
    else:
        print 'Unknown Query'


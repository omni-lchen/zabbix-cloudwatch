#!/usr/bin/env python

# Date:   06/11/2015
# Author: Long Chen
# Description: A script to bulk send cloudwatch metrics data by using python zabbix sender
# Requires Python Zabbix Sender: https://github.com/kmomberg/pyZabbixSender/blob/master/pyZabbixSender.py
# Example Usage: zabbixCloudWatch.py -z <zabbix_server> -x <zabbix_host> -a <aws_account> -r <aws_region> -s <aws_service> -d "<Dimension>" -p 300 -f "2015-08-13 04:00:00" -t "2015-08-13 04:15:00"

import os
import re
import sys
import time
import json
import fileinput
from dateutil import tz
from datetime import datetime
from optparse import OptionParser
from operator import itemgetter
from awsAccount import awsAccount
from awsConnection import awsConnection
from boto.exception import BotoServerError
from pyZabbixSender import pyZabbixSender

# aws services metrics configuration file
base_path = os.path.dirname(os.path.realpath(__file__))
aws_services_conf = base_path + '/conf/aws_services_metrics.conf'

# Config command line options
def config_parser():
    parser = OptionParser(usage="usage: %prog [options]", version="%prog 2.0")
    parser.add_option("-z", "--zabbix", dest="zabbixserver", help="zabbix server name", metavar="ZABBIX")
    parser.add_option("-x", "--host", dest="zabbixhost", help="zabbix host name", metavar="HOST")
    parser.add_option("-a", "--account", dest="accountname", help="account name", metavar="ACCOUNT")
    parser.add_option("-r", "--region", dest="region", help="aws region", metavar="REGION")
    parser.add_option("-s", "--service", dest="service", help="aws service (ELB, SQS, DynamoDB, etc...)", metavar="SERVICE")
    parser.add_option("-d", "--dimensions", dest="dimensions", help="Dimensions split with comma (LoadBalancerName=, etc...)", metavar="DIMENSIONS")
    parser.add_option("-p", "--period", dest="period", help="Period", metavar="PERIOD")
    parser.add_option("-f", "--starttime", dest="starttime", help="Start Time", metavar="STARTTIME")
    parser.add_option("-t", "--endtime", dest="endtime", help="End Time", metavar="ENDTIME")
    return parser

# Covert dimensions string to json format
def dimConvert(d):
    dim = {}
    # Split dimensions by comma
    firstSplit = d.split(',')
    for word in firstSplit:
        # Split dimension name and value by equal
        secondSplit = word.split('=')
        dim[secondSplit[0]] = secondSplit[1]
    return dim

# Convert timestamp from UTC to local time
def utcToLocaltimestamp(timestamp):
    from_zone = tz.tzutc()
    to_zone = tz.tzlocal()
    utctimestamp = timestamp.replace(tzinfo=from_zone)
    return utctimestamp.astimezone(to_zone)

# Get DynamoDB cloudwatch data
def getCloudWatchDynamodbData(a, r, s, t, i=None):
    account = a
    aws_account = awsAccount(account)
    aws_access_key_id = aws_account._aws_access_key_id
    aws_secret_access_key = aws_account._aws_secret_access_key
    aws_region = r
    aws_service = s
    table_name = t
    global_index = i

    namespace = 'AWS/' + aws_service
    operations_all = ['GetItem', 'PutItem', 'Query', 'Scan', 'UpdateItem', 'DeleteItem', 'BatchGetItem', 'BatchWriteItem']
    operations_returned_item = ['Query', 'Scan']

    global period
    global start_time
    global end_time
    # get_metric_statistics(period, start_time, end_time, metric_name, namespace, statistics, dimensions=None, unit=None)
    try:
        conn = awsConnection()
        conn.cloudwatchConnect(aws_region, aws_access_key_id, aws_secret_access_key)
        cw = conn._aws_connection

        # Read DynamoDB metrics
        aws_metrics = json.loads(open(aws_services_conf).read())

        # Initialize cloud watch data list for storing results
        cloud_watch_data = []

        for metric in aws_metrics[aws_service]:
            metric_name = metric['metric']
            statistics = metric['statistics']
            dimensions = {}

            if metric_name in ('SuccessfulRequestLatency', 'SystemErrors', 'ThrottledRequests'):
                for op in operations_all:
                    dimensions['TableName'] = table_name
                    dimensions['Operation'] = op
                    # Get cloudwatch data
                    results = cw.get_metric_statistics(period, start_time, end_time, metric_name, namespace, statistics, dimensions)
                    metric_results = {}
                    # Generate a zabbix trapper key for a metric
                    zabbix_key = 'DynamoDB.' + op + '.' + metric_name + '.' + statistics + '["' + account + '","' + aws_region + '","' + table_name + '"]'
                    metric_results['zabbix_key'] = zabbix_key
                    metric_results['cloud_watch_results'] = results
                    metric_results['statistics'] = statistics
                    cloud_watch_data.append(metric_results)
            elif metric_name == 'ReturnedItemCount':
                for op in operations_returned_item:
                    dimensions['TableName'] = table_name
                    dimensions['Operation'] = op
                    # Get cloudwatch data
                    results = cw.get_metric_statistics(period, start_time, end_time, metric_name, namespace, statistics, dimensions)
                    metric_results = {}
                    # Generate a zabbix trapper key for a metric
                    zabbix_key = 'DynamoDB.' + op + '.' + metric_name + '.' + statistics + '["' + account + '","' + aws_region + '","' + table_name + '"]'
                    metric_results['zabbix_key'] = zabbix_key
                    metric_results['cloud_watch_results'] = results
                    metric_results['statistics'] = statistics
                    cloud_watch_data.append(metric_results)
            elif metric_name in ('OnlineIndexConsumedWriteCapacity', 'OnlineIndexPercentageProgress', 'OnlineIndexThrottleEvents'):
                if global_index:
                    dimensions['TableName'] = table_name
                    dimensions['GlobalSecondaryIndexName'] = global_index
                    # Get cloudwatch data
                    results = cw.get_metric_statistics(period, start_time, end_time, metric_name, namespace, statistics, dimensions)
                    metric_results = {}
                    # Generate a zabbix trapper key for a metric
                    zabbix_key = 'DynamoDB.' +  metric_name + '.' + statistics + '["' + account + '","' + aws_region + '","' + table_name + '","' + global_index + '"]'
                    metric_results['zabbix_key'] = zabbix_key
                    metric_results['cloud_watch_results'] = results
                    metric_results['statistics'] = statistics
                    cloud_watch_data.append(metric_results)
            else:
                dimensions['TableName'] = table_name
                # Get cloudwatch data
                results = cw.get_metric_statistics(period, start_time, end_time, metric_name, namespace, statistics, dimensions)
                metric_results = {}
                # Generate a zabbix trapper key for a metric
                zabbix_key = 'DynamoDB.' +  metric_name + '.' + statistics + '["' + account + '","' + aws_region + '","' + table_name + '"]'
                metric_results['zabbix_key'] = zabbix_key
                metric_results['cloud_watch_results'] = results
                metric_results['statistics'] = statistics
                cloud_watch_data.append(metric_results)

        return cloud_watch_data

    except BotoServerError, error:
        print >> sys.stderr, 'CloudWatch ERROR: ', error

# Get cloudwatch metrics data of an AWS service
def getCloudWatchData(a, r, s, d):
    account = a
    aws_account = awsAccount(account)
    aws_access_key_id = aws_account._aws_access_key_id
    aws_secret_access_key = aws_account._aws_secret_access_key
    aws_region = r
    aws_service = s
    dimensions = d

    namespace = 'AWS/' + aws_service
    global period
    global start_time
    global end_time
    # get_metric_statistics(period, start_time, end_time, metric_name, namespace, statistics, dimensions=None, unit=None)
    try:
        conn = awsConnection()
        conn.cloudwatchConnect(aws_region, aws_access_key_id, aws_secret_access_key)
        cw = conn._aws_connection

        # Read AWS services metrics
        aws_metrics = json.loads(open(aws_services_conf).read())

        # Initialize cloud watch data list for storing results
        cloud_watch_data = []

        for metric in aws_metrics[aws_service]:
            metric_name = metric['metric']
            statistics = metric['statistics']
            # Get cloudwatch data
            results = cw.get_metric_statistics(period, start_time, end_time, metric_name, namespace, statistics, dimensions)

            metric_results = {}

            # Generate a zabbix trapper key for a metric
            if aws_service == 'SQS':
                queue_name = dimensions['QueueName']
                zabbix_key =  aws_service + '.' + metric_name + '.' + statistics + '["' + account + '","' + aws_region + '","' + queue_name + '"]'
            elif aws_service == 'SNS':
                topic_name = dimensions['TopicName']
                zabbix_key =  aws_service + '.' + metric_name + '.' + statistics + '["' + account + '","' + aws_region + '","' + topic_name + '"]'
            else:
                zabbix_key =  aws_service + '.' + metric_name + '.' + statistics

            metric_results['zabbix_key'] = zabbix_key
            metric_results['cloud_watch_results'] = results
            metric_results['statistics'] = statistics
            cloud_watch_data.append(metric_results)

        return cloud_watch_data

    except BotoServerError, error:
        print >> sys.stderr, 'CloudWatch ERROR: ', error

# Send latest cloudwatch data to zabbix server
def sendLatestCloudWatchData(z, h, d):
    zabbix_server = z
    zabbix_host = h
    cloud_watch_data = d

    global start_time

    zabbix_sender = pyZabbixSender(server=zabbix_server, port=10051)
    for cwdata in cloud_watch_data:
        zabbix_key = cwdata['zabbix_key']
        results = cwdata['cloud_watch_results']
        statistics = cwdata['statistics']

        if results:
            # sort results by timestamp in descending order
            sorts = sorted(results, key=itemgetter('Timestamp'), reverse=True)
            # Get the latest data and timestamp
            zabbix_key_value = sorts[0][statistics]
            zabbix_key_timestamp = int(time.mktime(utcToLocaltimestamp(sorts[0]['Timestamp']).timetuple()))
            # Add data to zabbix sender
            zabbix_sender.addData(zabbix_host, zabbix_key, zabbix_key_value, zabbix_key_timestamp)
        else:  # No data found within the time window
            # Set the zabbix key value to 0
            zabbix_key_value = 0
            # Set the zabbix key timestamp as the start time for getting cloudwatch data
            zabbix_key_timestamp = int(time.mktime(utcToLocaltimestamp(start_time).timetuple()))
            # Add data to zabbix sender
            zabbix_sender.addData(zabbix_host, zabbix_key, zabbix_key_value, zabbix_key_timestamp)

    # Send data to zabbix server
    #zabbix_sender.printData()
    zabbix_sender.sendData()

# Send all cloudwatch data to zabbix server
# init log file first by using this function "initCloudWatchLog"
# then purge old lines with this function "purgeOldCloudWatchLog"
# this function is good to be used for sending 1-min cloudwatch data every 5 minutes
def sendAllCloudWatchData(z, h, d, l):
    zabbix_server = z
    zabbix_host = h
    cloud_watch_data = d
    cw_log = l

    global start_time

    # Open cloudwatch log file for appending
    file = open(cw_log, 'a')

    zabbix_sender = pyZabbixSender(server=zabbix_server, port=10051)
    for cwdata in cloud_watch_data:
        zabbix_key = cwdata['zabbix_key']
        results = cwdata['cloud_watch_results']
        statistics = cwdata['statistics']

        if results:
            # sort results by timestamp in descending order
            sorts = sorted(results, key=itemgetter('Timestamp'), reverse=True)
            for sort in sorts:
                zabbix_key_value = sort[statistics]
                zabbix_key_timestamp = int(time.mktime(utcToLocaltimestamp(sorts[0]['Timestamp']).timetuple()))
                # Get cloudwatch data in the format of: <timestamp>,<key>,<value>
                cw_data = str(zabbix_key_timestamp) + ',' + str(zabbix_key) + ',' + str(zabbix_key_value)
                # Search cloudwatch log with timestamp and key, send cloudwatch data if it is not found in the log
                cw_data_search = str(zabbix_key_timestamp) + ',' + str(zabbix_key)
                # Add escape to square brackets for regular expression search, to fix search pattern error
                cw_data_search = cw_data_search.replace("[", "\[").replace("]", "\]")
                cw_data_found = 0
                for line in open(cw_log, 'r'):
                    if re.search(cw_data_search, line):
                        cw_data_found = cw_data_found + 1
                        break
                # If data not found in the cloudwatch log, then add new data
                if cw_data_found == 0:
                    # Add data to zabbix sender
                    zabbix_sender.addData(zabbix_host, zabbix_key, zabbix_key_value, zabbix_key_timestamp)
                    # Write cloudwatch data to the log file
                    file.write(cw_data + '\n')

        else:  # No data found within the time window
            # Set the zabbix key value to 0
            zabbix_key_value = 0
            # Set the zabbix key timestamp as the start time for getting cloudwatch data
            zabbix_key_timestamp = int(time.mktime(utcToLocaltimestamp(start_time).timetuple()))
            # Get cloudwatch data in the format of: <timestamp>,<key>,<value>
            cw_data = str(zabbix_key_timestamp) + ',' + str(zabbix_key) + ',' + str(zabbix_key_value)
            # Search cloudwatch log with timestamp and key, send cloudwatch data if it is not found in the log
            cw_data_search = str(zabbix_key_timestamp) + ',' + str(zabbix_key)
            # Add escape to square brackets for regular expression search, to fix search pattern error
            cw_data_search = cw_data_search.replace("[", "\[").replace("]", "\]")
            cw_data_found = 0
            for line in open(cw_log, 'r'):
                if re.search(cw_data_search, line):
                    cw_data_found = cw_data_found + 1
                    break
            # If data not found in the cloudwatch log, then add new data
            if cw_data_found == 0:
                # Set zabbix trapper key value to 0 if no data found in cloudwatch
                zabbix_sender.addData(zabbix_host, zabbix_key, zabbix_key_value, zabbix_key_timestamp)
                # Write cloudwatch data to the log file
                file.write(cw_data + '\n')

    # Send data to zabbix server
    #zabbix_sender.printData()
    send_results = zabbix_sender.sendData()
    file.write(str(send_results) + '\n')
    # Close cloudwatch log file
    file.close()

# Initialize cloudwatch log
def initCloudWatchLog(s, h, r):
    aws_service = s
    zabbix_host = h
    aws_region = r
    # Create a log file to save cloudwatch data
    cw_log = '/var/log/cloudwatch.' + aws_service + '.' + zabbix_host + '.' + aws_region + '.log'
    # Remove spaces from log file name
    cw_log = cw_log.replace(" ", "")
    return cw_log

# Purge old cloudwatch log, use together with these functions: "initCloudWatchLog" and "sendAllCloudWatchDataToZabbixSender"
def purgeOldCloudWatchLog(l, b):
    cw_log = l
    # Set how many lines to keep in the log file
    log_buffer = b
    # Count number of lines in cloudwatch log file
    number_of_lines = len(open(cw_log).readlines())
    # Last line number
    last_line = number_of_lines - log_buffer
    # Delete lines and keep the buffer lines
    if last_line > 0:
        for line_number, line in enumerate(fileinput.input(cw_log, inplace=1)):
            if line_number < last_line:
                continue
            else:
                sys.stdout.write(line)

if __name__ == '__main__':
    parser = config_parser()

    # Read options from parser
    (options, args) = parser.parse_args()
    zabbix_server = options.zabbixserver
    zabbix_host =  options.zabbixhost
    aws_account = options.accountname
    aws_region = options.region
    aws_service = options.service
    dimensions = dimConvert(options.dimensions)
    period = options.period

    # Set global start time and end time in cloudwatch
    start_time = datetime.strptime(options.starttime, "%Y-%m-%d %H:%M:%S")
    end_time = datetime.strptime(options.endtime, "%Y-%m-%d %H:%M:%S")

    if aws_service == 'DynamoDB':
        table_name = dimensions['TableName']
        # Get cloudwatch data of a DynamoDB table
        cw_data = getCloudWatchDynamodbData(aws_account, aws_region, aws_service, table_name)
        # Only use log buffer with "sendAllCloudWatchData" function
        # log buffer is used to check the cloudwatch history data,
        # set the number as low as possible to get the best performance,
        # but should be more than the total number of monitoring items of the aws service in the host
        ##log_buffer = 1000
    else:
        # Get cloudwatch data of an AWS service
        cw_data = getCloudWatchData(aws_account, aws_region, aws_service, dimensions)
        # Only use log buffer with "sendAllCloudWatchData" function
        # log buffer is used to check the cloudwatch history data,
        # set the number as low as possible to get the best performance,
        # but should be more than the total number of monitoring items of the aws service in the host
        ##log_buffer = 500

    # Send latest cloudwatch data with zabbix sender
    sendLatestCloudWatchData(zabbix_server, zabbix_host, cw_data)

    # Send all cloudwatch data in a specified time window with zabbix sender
    #cw_log = initCloudWatchLog(aws_service, zabbix_host, aws_region)
    #sendAllCloudWatchData(zabbix_server, zabbix_host, cw_data, cw_log)
    #purgeOldCloudWatchLog(cw_log, log_buffer)

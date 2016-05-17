# zabbix-cloudwatch
Amazon CloudWatch is a monitoring service for AWS cloud resources and the applications you run on AWS, which can be accessed from AWS console. We have now integrated CloudWatch monitoring data into Zabbix monitoring system.

AmazonCloudWatch Developer Guide - http://docs.aws.amazon.com/AmazonCloudWatch/latest/DeveloperGuide/supported_services.html

AWS SDK in Python Boto - https://github.com/boto/boto

# Installation
1. Install boto on zabbix server via pip.
   * pip install boto
   
1. Find the metrics from AmazonCloudWatch Developer Guide and add metrics to the configuration file "conf/aws_services_metrics.conf".

2. Create a zabbix template for an AWS service, then create items with metrics key by using zabbix trapper type.

  AWS Metric Zabbix Trapper Item Key Format without Discovery
  Key: \<aws_service\>.\<metric\>.\<statistics\>

  AWS Metric Zabbix Trapper Item Key Format with Discovery
  Key: \<aws_service\>.\<metric\>.\<statistics\>["\<aws_account\>","\<aws_region\>","\<discovery_item_value\>"]

  DynamoDB Item Key Format is different from the standard setup, due to combinations of different dimensions and metrics.
  operations_all = ['GetItem', 'PutItem', 'Query', 'Scan', 'UpdateItem', 'DeleteItem', 'BatchGetItem', 'BatchWriteItem']
  operations_metrics = ['SuccessfulRequestLatency', 'SystemErrors', 'ThrottledRequests]
  DynamoDB Item Key1: DynamoDB.\<operations_all\>.\<operations_metrics\>.\<statistics\>["\<aws_account\>","\<aws_region\>","\<table_name\>"]

  operations_returned_item = ['Query', 'Scan']
  DynamoDB Item Key2: DynamoDB.\<operations_returned_item\>.ReturnedItemCount.\<statistics\>["\<aws_account\>","\<aws_region\>","\<table_name\>"]

  DynamoDB Other Keys: DynamoDB.\<metric\>.\<statistics\>["\<aws_account\>","\<aws_region\>","\<table_name\>"]

3. Create a new host and linked with the template.

4. Create a cloudwatch bash wrapper script for cron job.

5. Create a new cron job to send the cloudwatch metrics to the host.
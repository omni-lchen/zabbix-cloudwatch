# Date:   03/08/2015
# Author: Long Chen
# Description: A class to establish connections to aws services

import boto.ec2.cloudwatch
import boto.ec2.elb
import boto.sqs
import boto.rds
import boto.dynamodb
import boto.redshift
import boto.sns
import boto.route53

class awsConnection:
    _aws_connection = None

    def __init__(self):
        _aws_connection = None

    # CloudWatch connection
    def cloudwatchConnect(self, region, access_key, secret_key):
        self._aws_connection = boto.ec2.cloudwatch.connect_to_region(region, aws_access_key_id=access_key, aws_secret_access_key=secret_key)

    # ELB connection
    def elbConnect(self, region, access_key, secret_key):
        self._aws_connection = boto.ec2.elb.connect_to_region(region, aws_access_key_id=access_key, aws_secret_access_key=secret_key)

    # SQS connection
    def sqsConnect(self, region, access_key, secret_key):
        self._aws_connection = boto.sqs.connect_to_region(region, aws_access_key_id=access_key, aws_secret_access_key=secret_key)

    # RDS connection
    def rdsConnect(self, region, access_key, secret_key):
        self._aws_connection = boto.sqs.connect_to_region(region, aws_access_key_id=access_key, aws_secret_access_key=secret_key)

    # DynamoDB connection
    def dynamodbConnect(self, region, access_key, secret_key):
        self._aws_connection = boto.dynamodb.connect_to_region(region, aws_access_key_id=access_key, aws_secret_access_key=secret_key)

    # Redshift connection
    def redshiftConnect(self, region, access_key, secret_key):
        self._aws_connection = boto.redshift.connect_to_region(region, aws_access_key_id=access_key, aws_secret_access_key=secret_key)

    # SNS connection
    def snsConnect(self, region, access_key, secret_key):
        self._aws_connection = boto.sns.connect_to_region(region, aws_access_key_id=access_key, aws_secret_access_key=secret_key)

    # Route53 connection
    def route53Connect(self, region, access_key, secret_key):
        self._aws_connection = boto.route53.connect_to_region(region, aws_access_key_id=access_key, aws_secret_access_key=secret_key)

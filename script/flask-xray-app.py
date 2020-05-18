# Import the X-Ray modules
from aws_xray_sdk.ext.flask.middleware import XRayMiddleware
from aws_xray_sdk.core import patcher, xray_recorder
from flask import Flask
import requests
import boto3
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr
import decimal
import json
import os
import awsgi

CURRENT_REGION = os.environ["AWS_REGION"]
s3_client = boto3.client(
    's3',
    region_name=CURRENT_REGION
)

dynamodb_client = boto3.client('dynamodb', region_name=CURRENT_REGION)

# Patch the requests module to enable automatic instrumentation
patcher.patch(('requests',))

app = Flask(__name__)

# Configure the X-Ray recorder to generate segments with our service name
xray_recorder.configure(service='My First Serverless App')

# Instrument the Flask application
XRayMiddleware(app, xray_recorder)

@app.route('/')
def hello_world():
    resp = requests.get("https://aws.amazon.com")
    return 'Hello, World: %s' % resp.url

# Use decorators to automatically set the subsegments
@xray_recorder.capture('put_object_into_s3')
def put_object_into_s3():
    try:
        response = s3_client.download_file(
            "aws-xray-assets.cn-northwest-1", "samples/aws-xray-sample-template.yaml", "aws-xray-sample-template.yaml")
        status_code = response['ResponseMetadata']['HTTPStatusCode']
        xray_recorder.current_subsegment().put_annotation('put_response', status_code)
    except ClientError as e:
        print(e)
        return {
            'statusCode': 500,
            'body': 's3 operation failed: ' + e.response['Error']['Message']
        }

# Define subsegments manually
def handle_ddb():
    xray_recorder.begin_subsegment('handle_ddb')
    DDB_TABLE_NAME = 'Movies'
    try:
        response = dynamodb_client.describe_table(TableName=DDB_TABLE_NAME)
    except dynamodb_client.exceptions.ResourceNotFoundException:
        try:
            table = dynamodb_client.create_table(
                TableName=DDB_TABLE_NAME,
                KeySchema=[
                    {
                        'AttributeName': 'year',
                        'KeyType': 'HASH'  # Partition key
                    },
                    {
                        'AttributeName': 'title',
                        'KeyType': 'RANGE'  # Sort key
                    }
                ],
                AttributeDefinitions=[
                    {
                        'AttributeName': 'year',
                        'AttributeType': 'N'
                    },
                    {
                        'AttributeName': 'title',
                        'AttributeType': 'S'
                    },

                ],
                ProvisionedThroughput={
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5
                }
            )
            dynamodb_client.get_waiter('table_exists').wait(TableName=DDB_TABLE_NAME)
            print("Table status:", table)
        except ClientError as e:
            print(e)
            return {
                'statusCode': 500,
                'body': 'create ddb table Movies failed: ' + e.response['Error']['Message']
            }
        pass
        

    title = "The Big New Movie"
    year = 2015

    try:
        response = dynamodb_client.put_item(
            TableName=DDB_TABLE_NAME,
            Item={
                'year': {'N': str(year)},
                'title': {'S': title},
                'info': {
                    'M':{
                        'plot': {'S': "Nothing happens at all."},
                        'rating': {'N': str(decimal.Decimal(0))}
                    }
                }
            }
        )
        print("PutItem succeeded:")
        print(json.dumps(response, indent=4))
        xray_recorder.current_subsegment().put_annotation('get_response', response)
    except ClientError as e:
        print(e)
        return {
            'statusCode': 500,
            'body': 'ddb put_item failed: ' + e.response['Error']['Message']
        }


    try:
        response = dynamodb_client.get_item(
            TableName=DDB_TABLE_NAME,
            Key={
                'year': {'N': str(year)},
                'title': {'S': title}
            }
        )
        item = response['Item']
        print("GetItem succeeded:")
        print(json.dumps(item, indent=4))
    except ClientError as e:
        print(e)
        return {
            'statusCode': 500,
            'body': 'ddb get_item failed: ' + e.response['Error']['Message']
        }
    xray_recorder.end_subsegment()

@app.route('/app')
def hello_app():
    xray_recorder.begin_segment('hello_app')

    # bing
    xray_recorder.begin_subsegment('call bing')
    resp = requests.get("https://www.bing.com")
    print('Hello, app: %s' % resp.url)
    xray_recorder.end_subsegment()

    # s3 
    put_object_into_s3()
    
    # DynamoDB
    handle_ddb()
    
    # response
    xray_recorder.begin_subsegment('response')
    body = {
        "message": "Go Serverless v1.0! Your function executed successfully!"
    }

    response = {
        "statusCode": 200,
        "body": json.dumps(body)
    }

    xray_recorder.end_subsegment()
    xray_recorder.end_segment()

    return response

def lambda_handler(event, context):
    return awsgi.response(app, event, context)
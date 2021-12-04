#!/usr/bin/python3

import os
import sys
import pprint
import logging
import json
import boto3
import datetime
from datetime import datetime
from decimal import Decimal
import base64
from botocore.exceptions import ClientError

from pyflowater import PyFlo

def setup_logger():
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
def get_credentials():
    secret_name = "flo"
    region_name = "us-east-1"

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    # In this sample we only handle the specific exceptions for the 'GetSecretValue' API.
    # See https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
    # We rethrow the exception by default.

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        if e.response['Error']['Code'] == 'DecryptionFailureException':
            # Secrets Manager can't decrypt the protected secret text using the provided KMS key.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InternalServiceErrorException':
            # An error occurred on the server side.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InvalidParameterException':
            # You provided an invalid value for a parameter.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InvalidRequestException':
            # You provided a parameter value that is not valid for the current state of the resource.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'ResourceNotFoundException':
            # We can't find the resource that you asked for.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
            
    response = json.loads(get_secret_value_response['SecretString'])
    username = response['username']
    pw = response['password']
    
    return username, pw
    
def add_to_dynamodb(consumption):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(os.environ['DYNAMODB_TABLE'])

    for item in consumption['items']:
        table.put_item(
           Item={
                'date': item['time'][0:10],
                'timestamp': item['time'],
                'type': 'flo',
                'gallonsConsumed' : Decimal(str(item['gallonsConsumed']))
            }
)

def main(event, handler):
    user, password = get_credentials()

    if (user == None) or (password == None):
        print("ERROR! Must define variables FLO_USER and FLO_PASSWORD in SecretsManager")
        raise SystemExit

    #setup_logger()
    pp = pprint.PrettyPrinter(indent = 2)
 
    flo = PyFlo(user, password)

    print(f"User = #{flo.user_id}")

    print("\n--Data--")
    pp.pprint( flo.data() )

    print("\n--Locations--")
    locations = flo.locations()
    pp.pprint( locations )

    print("\n--Single Location--")
    location_info = locations[0]
    location_id = location_info['id']    
    pp.pprint( flo.location(location_id) )

    for location in locations:
        print(f"\n--Location {location['id']}--")

        for device in location['devices']:
            id = device['id']
        
            print("\n--Devices--")
            pp.pprint( device )
    
            print("\n--Device Info--")
            pp.pprint( flo.device(id) )

            print("\n--Consumption--")
            pp.pprint( flo.consumption(id))
            add_to_dynamodb(flo.consumption(id))

if __name__ == "__main__":
    main(None, None)

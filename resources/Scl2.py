#!/usr/bin/python3

import datetime
import json
import requests
import boto3
import os

class Source:
    def __init__(self, street_address, username, password):
        self._street_address = street_address
        self._username = username
        self._password = password

    def fetch(self):
        # step 3
        token_payload = {
            "grant_type": "password",
            "username": self._username,
            "password": self._password,
        }

        r = requests.post(
            "https://myutilities.seattle.gov/rest/auth/token", data=token_payload
        )

        token_info = json.loads(r.text)
        token = token_info["access_token"]

        headers = {"Authorization": f"Bearer {token}"}

        # step 4
        swsummary_payload = {
            "customerId": "2489663",
            "port": "2212797",
            "startDate": (datetime.datetime.today() + datetime.timedelta(days=-7)).strftime('%m/%d/%Y'),
            "endDate": datetime.datetime.today().strftime('%m/%d/%Y'),
            "accountContext": {
                "accountNumber": 5287487360,
                "serviceId": "2212797#5286585771"
            },
        }

        r = requests.post(
            "https://myutilities.seattle.gov/rest/usage/month",
            json=swsummary_payload,
            headers=headers,
        )
        summary_info = json.loads(r.text)
        add_to_dynamodb(summary_info['history'])

def add_to_dynamodb(items):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(os.environ['DYNAMODB_TABLE'])

    for item in items:
        table.put_item(
           Item={
                'date': item['chargeDateRaw'],
                'timestamp': item['chargeDateRaw'],
                'type': 'scl',
                'gallonsConsumed' : item['billedConsumption']
            }
)
def get_credentials():
    secret_name = "scl"
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

def main(event, context):
    username, password = get_credentials()
    a = Source('10048 40th Ave NE', username, password)
    a.fetch()

if __name__ == "__main__":
    main(None, None)

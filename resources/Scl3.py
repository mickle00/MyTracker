#!/usr/bin/python3

import datetime
import json
import requests
import boto3
import os
from html.parser import HTMLParser
import base64

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
    
class MyHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.dict = {}

    def handle_starttag(self, tag, attrs):
        if tag == "form":
            for attr in attrs:
                if attr[0] == "action":
                    self.url = attr[1]

        if tag == "input":
            for attr in attrs:
                if "name" in attr:
                    self.name = attr[1]
                if "value" in attr:
                    self.value = attr[1]

    def handle_endtag(self, tag):
        if tag != "input":
            return

        self.dict[self.name] = self.value

        self.name = None
        self.value = None

    def get_form_data(self):
        return self.dict

    def get_form_url(self):
        return self.url

class SeattleCityLight:
    username, password = get_credentials()
    accept_html = "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
    
    def submit_form(self, url, data, cookie=None):
        if cookie == None:
            headers = None
        else:
            headers = {"Cookie": cookie}
            
        r = requests.post(
            url,
            headers=headers,
            data=data,
            allow_redirects = False
        )
        
        return r
    
    def get_data_from_js(self, data):
        startIDX = data.find("setItem")
        idx1 = data.find("(", startIDX) + 1
        idx2 = data.find(")", idx1)

        startIDX = data.find("setItem", idx1)
        idx1 = data.find("(", startIDX) + 1
        idx2 = data.find(")", idx1)

        signinAt = data[idx1:idx2].split(
            ",")[1].replace(' ', '').replace('"', '')

        startIDX = data.find("setItem", idx1)
        idx1 = data.find("(", startIDX) + 1
        idx2 = data.find(")", idx1)

        baseUri = data[idx1:idx2].split(
            ",")[1][1:-1].replace(' ', '').replace('"', '')

        startIDX = data.find("setItem", idx1)
        idx1 = data.find("(", startIDX) + 1
        idx2 = data.find(")", idx1)

        clientId = data[idx1:idx2].split(
            ",")[1][1:-1].replace(' ', '').replace('"', '')

        startIDX = data.find("setItem", idx1)
        idx1 = data.find("(", startIDX) + 1
        idx2 = data.find(")", idx1)

        initialState = data[idx1:idx2].split(
            ",")[1][1:-1].replace(' ', '').replace('"', '')

        startIDX = data.find("setItem", idx1)
        idx1 = data.find("(", startIDX) + 1
        idx2 = data.find(")", idx1)

        commaIDX = data[idx1:idx2].find(",")

        initialState = data[idx1:idx2][commaIDX+1:]

        return {
            "signinAT": signinAt,
            "baseUri": baseUri,
            "initialState": json.loads(initialState[1:-1])
        }
        
    
    def do_authenticate(self, jsdata):
        json = {
            "credentials": {
                "password": self.password,
                "username": self.username,
            },
            "signinAT": jsdata["signinAT"],
            "initialState": jsdata["initialState"]
        }
        headers = {"Content-Type": "application/json"}
        data = requests.post(
            "https://login.seattle.gov/authenticate", 
            json=json,
            headers=headers)
        return data.json()
    
    def start_session(self, baseuri, authnToken, cookie):
        body = {"authnToken": authnToken}
        headers = {"Cookie": cookie}
        url = "{}/sso/v1/sdk/session".format(baseuri)
        return requests.post(
            url, 
            data=body,
            headers=headers, allow_redirects=False
        )
    
    def add_to_dynamodb(self, items):
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(os.environ['DYNAMODB_TABLE'])

        for item in items:
            ## API returns all days in a month, but will zero value for non-requested days
            if (item['billedConsumption']) == '0.0':
                ##print(item)
                continue
            print(item)
            table.put_item(
               Item={
                    'date': item['chargeDateRaw'],
                    'timestamp': item['chargeDateRaw'],
                    'type': 'scl',
                    'kWhUsed' : item['billedConsumption']
                }
            )
                    
    def get_usage(self):
        headers = {"Authorization": f"Bearer {self.token}"}

        r = requests.get(
            "https://myutilities.seattle.gov/eportal/#/billingoverview",
            headers = headers
        )
        
        swsummary_payload = {
            "customerId": "2489663",
            "port": "2212797",
            "startDate": (datetime.datetime.today() + datetime.timedelta(days=-30)).strftime('%m/%d/%Y'),
            "endDate": datetime.datetime.today().strftime('%m/%d/%Y'),
            "accountContext": {
                "accountNumber": 5287487360,
                "serviceId": "2212797#5286585771"
            },
        }

        r = requests.post(
            "https://myutilities.seattle.gov/rest/usage/month",
            json=swsummary_payload,
            headers = headers
        )
        summary_info = json.loads(r.text)
        self.add_to_dynamodb(summary_info['history'])
    
    def login(self):
        r = requests.get(
            "https://myutilities.seattle.gov/rest/auth/ssologin",
            allow_redirects = False
        )
        self.oracle_location = r.headers['Location']
    
        r = requests.get(self.oracle_location,
            allow_redirects = False
        )
        self.oracle_cookie = r.headers['Set-Cookie']
        self.oracle_login_url = r.headers['Location']
        self.oracle_location_html = r.text
        
        headers = {"Cookie": self.oracle_cookie}
        r = requests.get(self.oracle_location, headers = headers)
        
        self.oracle_html_form = r.text
        
        parser = MyHTMLParser()
        parser.feed(self.oracle_html_form)
        data = parser.get_form_data()
        url = parser.get_form_url()
        
        data = self.submit_form(url, data)
        jsdata = self.get_data_from_js(data.text)
        
        data = self.do_authenticate(jsdata)

        data = self.start_session(jsdata["baseUri"], data["authnToken"], self.oracle_cookie)
        cookie = data.headers["set-Cookie"]
        
        text =  data.text
        parser = MyHTMLParser()
        parser.feed(text)

        data = parser.get_form_data()
        url = parser.get_form_url()

        data = self.submit_form(url, data, cookie)
        cookie = data.headers["Set-Cookie"]

        text = data.text
        parser = MyHTMLParser()
        parser.feed(text)

        data = parser.get_form_data()
        url = parser.get_form_url()

        form_data = self.submit_form(url, data, cookie)
        sso_url = form_data.headers["Location"]
        
        auth_payload = {
            "grant_type": "authorization_code",
            "logintype" : "sso",
            "usertoken": sso_url.split('/')[-1]
        }
        
        r = requests.get(form_data.headers["Location"])
        self.auth_data = requests.post('https://myutilities.seattle.gov/rest/auth/token', data=auth_payload).json()
        self.token = self.auth_data['access_token']
       
def main(event, context):
    scl = SeattleCityLight()
    scl.login()
    scl.get_usage()

if __name__ == "__main__":
    main(None, None)
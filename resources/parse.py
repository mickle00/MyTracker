#!/usr/local/bin/python3

import requests
import datetime
import boto3
from bs4 import BeautifulSoup
from datetime import datetime
from decimal import Decimal
from re import sub
import os

req_headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'accept-encoding': 'gzip, deflate, br',
    'accept-language': 'en-US,en;q=0.8',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36'
}

def scrape():
    print('Scraping!')
    try:
        url = "https://www.zillow.com/homedetails/10048-40th-Ave-NE-Seattle-WA-98125/48960558_zpid/"
        req = requests.get(url, headers = req_headers)
        bsObj = BeautifulSoup(req.text, "html.parser")
        return bsObj
    except Exception as e:
       print(e)

def get_zestimate(bsObj):
      for button in bsObj.findAll("button"):
          if ('Zestimate' in button.text):
            print(button)
            zestimate = button.next_sibling.next_sibling.text
            print(zestimate)
            return zestimate

def send_message(message):
    client = boto3.client('sns')
    response = client.publish(
                TargetArn=os.environ['SNS_TOPIC'],
                Message=message,
                MessageStructure='text')

def add_to_dynamodb(estimate):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(os.environ['DYNAMODB_TABLE'])
    table.put_item(
       Item={
            'date': datetime.today().strftime('%Y-%m-%d'),
            'timestamp': datetime.now().isoformat(),
            'estimate' : Decimal(sub(r'[^\d.]', '', estimate)),
            'type': 'zestimate'
        }
)

def main(event, handler):
    estimate = get_zestimate(scrape())
    send_message('Current estimate is: ' + estimate);
    add_to_dynamodb(estimate)
    print(estimate);

if __name__ == "__main__":
    main(None,None)


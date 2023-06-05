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
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-encoding': 'gzip, deflate, br',
    'authority': 'www.zillow.com',
    'accept-language': 'en-US,en;q=0.8',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36',
    'sec-ch-ua': '"Google Chrome";v="113", "Chromium";v="113", "Not-A.Brand";v="24"',
    'sec-ch-ua-mobile': '?0' ,
    'sec-ch-ua-platform': '"macOS"' ,
    'sec-fetch-dest': 'document' ,
    'sec-fetch-mode': 'navigate' ,
    'sec-fetch-site': 'same-origin' ,
    'sec-fetch-user': '?1'
}

def scrape():
    print('Scraping!')
    try:
        url = "https://www.zillow.com/homedetails/10048-40th-Ave-NE-Seattle-WA-98125/48960558_zpid/"
        req = requests.get(url, headers = req_headers)
        bsObj = BeautifulSoup(req.text, "html.parser")
        return bsObj
    except Exception as e:
       print('Exception')
       print(e)
    print('end scrape')

def get_zestimate(bsObj):
      print(bsObj)
      print('iterating through buttons')
      for button in bsObj.findAll("button"):
          print(button)
          if ('Zestimate' in button.text):
            print('Zestimate button')
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


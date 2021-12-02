#!/usr/local/bin/python3

import requests
import datetime
import boto3
from bs4 import BeautifulSoup

req_headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'accept-encoding': 'gzip, deflate, br',
    'accept-language': 'en-US,en;q=0.8',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36'
}

def scrape():
    try:
        url = "https://www.zillow.com/homedetails/10048-40th-Ave-NE-Seattle-WA-98125/48960558_zpid/"
        req = requests.get(url, headers = req_headers)
        bsObj = BeautifulSoup(req.text, "html.parser")
        return bsObj
    except Exception as e:
       print(e)

def get_zestimate(bsObj):
      button = bsObj.find('button', id = 'dsChipZestimateTooltip')
      return button.next_sibling.next_sibling.text

def send_message(message):
    client = boto3.client('sns')
    response = client.publish(
                TargetArn='arn:aws:sns:us-east-1:729203071173:TestTopic2',
                Message=message,
                MessageStructure='text')

def main(event, handler):
    estimate = get_zestimate(scrape())
    send_message('Current estimate is: ' + estimate);
    print(estimate);

if __name__ == "__main__":
    main(None,None)


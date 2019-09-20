#!/usr/bin/env python3
import requests
from contextlib import closing
from bs4 import BeautifulSoup
import pprint as pp
import json

config_path = '_credentials/config.json'
def read_config():
    with open(config_path) as json_file:
        return json.load(json_file)

config = read_config()['foodsoft']
login_url = config['url']

with requests.Session() as s:
    #headers={"Content-Type":"application/x-www-form-urlencoded",
    #        "Host":"angel.co",
    #        "Origin":"https://angel.co"\,
    #        "User-Agent":"Mozilla/5.0 (Windows NT 6.1; WOW64)AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36"} # Mostly you need to pass the headers . Default headers don't work always.  So be careful here
    headers= {
'Host': 'app.foodcoops.at',
'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:69.0) Gecko/20100101 Firefox/69.0',
'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
'Accept-Language': 'de-AT,en-US;q=0.7,en;q=0.3',
'Accept-Encoding': 'gzip, deflate, br',
'Content-Type':'application/x-www-form-urlencoded',
            }
    r1 = s.get(login_url, headers=headers)
    html = BeautifulSoup(r1.content, 'html.parser' )
    headers['Referer'] = login_url
    headers['Upgrade-Insecure-Requests'] = '1'
    login_data = {
            'utf8': '%25E2%259C%2593', #'true'
            'authenticity_token' : '',
            'nick' : config['user'],
            'password' : config['password'],
            'commit' : 'Anmelden'}
    login_data['authenticity_token'] = html.find(attrs={'name': 'authenticity_token'})['value']
    response = s.post(login_url, headers = headers, data = login_data, cookies=r1.cookies)
    print(response.status_code)
#pp.pprint(vars(raw_html))
#print(raw_html.content)
#print(len(raw_html))
#html = BeautifulSoup(raw_html, 'html.parser')
#print(html.select('title'))



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
request_url = config['url'] + 'login'
login_url = config['url'] + 'sessions'
request_message_url = config['url'] + 'messages/new?message%5Bmail_to%5D=315'
send_message_url = config['url'] + 'messages'

with requests.Session() as s:
    #headers={"Content-Type":"application/x-www-form-urlencoded",
    #        "Host":"angel.co",
    #        "Origin":"https://angel.co"\,
    #        "User-Agent":"Mozilla/5.0 (Windows NT 6.1; WOW64)AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36"} # Mostly you need to pass the headers . Default headers don't work always.  So be careful here
    headers= {
'Host': 'app.foodcoops.at',
'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:69.0) Gecko/20100101 Firefox/69.0',
'Content-Type':'application/x-www-form-urlencoded',
            }
    r1 = s.get(request_url, headers=headers)
    html = BeautifulSoup(r1.content, 'html.parser' )
    headers['Referer'] = request_url
    headers['Upgrade-Insecure-Requests'] = '1'
    login_data = {
            'utf8': '%25E2%259C%2593', #'true'
            'authenticity_token' : '',
            'nick' : config['user'],
            'password' : config['password'],
            'commit' : 'Anmelden'}
    login_data['authenticity_token'] = html.find(attrs={'name': 'authenticity_token'})['value']
    print(login_data['authenticity_token'])
    response = s.post(login_url, headers = headers, data = login_data, cookies=r1.cookies)
    print('Response send login (POST): ' + str(response.status_code))
    r1 = s.get(request_message_url, headers=headers)
    print('Response message form (GET): ' + str(r1.status_code))
    html = BeautifulSoup(r1.content, 'html.parser')
    token = html.find(attrs={'name':'csrf-token'})['content']
    print(token)
    message = {
            'utf8': '%25E2%259C%2593',
            #'authenticity_token':str(token),
            'message[reply_to]':'',
            'message[send_methode]':'recipients',
            'message[workgroup_id]':'1',
            'message[ordergroup_id]':'162',
            'message[order_id]':'1472',
            'message[recipient_tokens]':'315',
            'message[private]':['0','1'],
            'message[subject]':'test-subject',
            'message[body]':'test',
            'commit':'Nachricht+verschicken'
            }
    headers['Referer'] = request_message_url
    response = s.post(send_message_url, headers=headers, data=message, cookies=r1.cookies)
    #print(html.contents)
    print('Response send message (POST): ' + str(response.status_code))
   


    #pp.pprint(vars(html))
    #print(html.contents)
#print(len(raw_html))
#html = BeautifulSoup(raw_html, 'html.parser')
#print(html.select('title'))



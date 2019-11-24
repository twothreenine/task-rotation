#This should work as an object API to connect with foodsoft and
#work with it.

from json import dumps
import logging
import requests
from bs4 import BeautifulSoup as bs

logging.basicConfig(level=logging.DEBUG)

class FSConnector:
    def __init__(self, url, user=None, password=None):
        self._session = None
        self._url = url # logging purpose only?
        self._url_login_request = url + 'login'
        self._url_login_post = url + 'sessions'
        self._url_mail_send = url + 'messages'
        self._url_mail_request = self._url_mail_send + '/new'

        self._default_header = {
                'Host': 'app.foodcoops.at',
                'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:69.0) Gecko/20100101 Firefox/69.0',
                'Content-Type':'application/x-www-form-urlencoded',
                'Upgrade-Insecure-Requests':'1'
                }

        self._login_data = {
                "utf8":"✓",
                'commit' : 'Anmelden'
                }

        if user and password:
            self.login(user, password)

    def _get(self, url, header, data=None):
        if data is None:
            response = self._session.get(url, headers=header)
        if response.status_code is not 200:
            self._session.close()
            logging.error('ERROR ' + str(response.status_code) + ' during GET ' + url)
            raise ConnectionError('Cannot get: ' +url)

        return response

    def _get_auth_token(self, response):
        if response is None:
            logging.error('ERROR failed to fetch authenticity_token')
            return ''
#        html = bs(response.content, 'html.parser')
#        auth_token =  html.find(attrs={'name':'authenticity_token'})
#        return auth_token['value']
        return bs(response.content, 'html.parser').find(attrs={'name':'authenticity_token'})['value']

    def _post(self, url, header, data, cookie):
        response = self._session.post(url, headers=header, data=data, cookies=cookie)
        if response.status_code is not 200: #302
            logging.error('Error ' + str(response.status_code) + ' during POST ' + url)
            raise ConnectionError('Error cannot post to ' + url)

        return response


    def login(self, user, password):
        self._user = user
        self._login_data['nick'] = user
        self._login_data['password'] = password

        login_header = self._default_header

        self._session = requests.Session()
        response = self._get(self._url_login_request, login_header)

        self._login_data['authenticity_token'] = self._get_auth_token(response)
        login_header['Referer'] = self._url_login_request

        response = self._post(self._url_login_post, login_header, self._login_data, response.cookies)
        logging.debug(user + ' logged in sucessfully to ' + self._url)
        
        
    def sendMailToRecipients(self, userIds, data):
        mail_header = self._default_header

        response = self._get(self._url_mail_request, mail_header)

        msg_data = {
            "utf8":"✓",
            "message[reply_to]":"",
            "message[send_method]":"recipients",
            "message[workgroup_id]":"0",
            "message[ordergroup_id]":"0",
            "message[order_id]":"0",
            "message[recipient_tokens]":",".join(map(str,userIds)),
            "message[private]":["0","1"],
            "message[subject]":data["subject"],
            "message[body]":data["body"],
            "commit":"Nachricht+verschicken"
            }
        mail_header["Referer"] = self._url_mail_request
        response = self._post(self._url_mail_send, mail_header, msg_data, response.cookies)
        logging.debug("Sent messages to " + ",".join(map(str,userIds)) + " with msg_data: " + dumps(msg_data, indent=2))




















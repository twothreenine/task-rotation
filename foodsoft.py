#This should work as an object API to connect with foodsoft and
#work with it.

from json import dumps
import logging
import requests
from bs4 import BeautifulSoup as bs
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service as FirefoxService
from webdriver_manager.firefox import GeckoDriverManager

logging.basicConfig(level=logging.DEBUG)

class User:
    def __init__(self, id, details, message_link=None, phone_number=None):
        self.id = id
        self.nick = details.get("nick")
        self.name = details.get("name")
        self.e_mail = details.get("email")
        self.phone_number = details.get("phone")
        self.message_link = message_link

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

    def _get(self, url, header, response=None):
        while response is None: # TODO: max retries instead of endless loop?
            try:
                response = self._session.get(url, headers=header)
            except requests.exceptions.ConnectionError:
                print("requests.exceptions.ConnectionError, waiting 3 seconds and trying again ...")
                time.sleep(3)
        if response.status_code != 200:
            self._session.close()
            logging.error('ERROR ' + str(response.status_code) + ' during GET ' + url)
            raise ConnectionError('Cannot get: ' +url)

        return response

    def _get_auth_token(self, request_content):
        if request_content is None:
            logging.error('ERROR failed to fetch authenticity_token')
            return ''
#        html = bs(response.content, 'html.parser')
#        auth_token =  html.find(attrs={'name':'authenticity_token'})
#        return auth_token['value']
        return bs(request_content, 'html.parser').find(attrs={'name':'authenticity_token'})['value']

    def _post(self, url, header, data, request):
        data['authenticity_token'] = self._get_auth_token(request.content)
        response = self._session.post(url, headers=header, data=data, cookies=request.cookies)
        if response.status_code != 200: #302
            logging.error('Error ' + str(response.status_code) + ' during POST ' + url)
            raise ConnectionError('Error cannot post to ' + url)

        return response


    def login(self, user, password):
        self._user = user
        self._login_data['nick'] = user
        self._login_data['password'] = password

        login_header = self._default_header

        self._session = requests.Session()
        request = self._get(self._url_login_request, login_header)

        login_header['Referer'] = self._url_login_request

        response = self._post(self._url_login_post, login_header, self._login_data, request)
        logging.debug(user + ' logged in sucessfully to ' + self._url)

    def logout(self):
        self._session.close()

    def open_driver(self):
        driver = webdriver.Firefox(service=FirefoxService(GeckoDriverManager().install()))
        driver.get(self._url)
        for cookie in self._session.cookies:
            driver.add_cookie({
                'name': cookie.name,
                'value': cookie.value,
                'path': cookie.path,
                'expiry': cookie.expires,
            })
        return driver
        
    def sendMailToRecipients(self, userIds, data):
        mail_header = self._default_header

        response = self._get(self._url_mail_request, mail_header)

        msg_data = {
            "utf8":"%25E2%259C%2593",#"✓",
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
        response = self._post(self._url_mail_send, mail_header, msg_data, response)
        logging.debug("Sent messages to " + ",".join(map(str,userIds)) + " header= " + str(response.request.headers) + " data= " + str(msg_data))

    def get_user_data(self):
        # Returns a list of all users (as User objects) containing their data
        users = []
        page = 1
        while page:
            userlist_url = f"{self._url}foodcoop?page={str(page)}&per_page=500"
            parsed_html = bs(self._get(userlist_url, self._default_header).content, 'html.parser') # do we need html5lib here?
            users_div = parsed_html.body.find("div", id="users")
            table_head = users_div.find("thead").find("tr").find_all("th")
            head_columns = list()
            for head_column in table_head:
                if head_column.find("a"):
                    head_columns.append(head_column.find("a").get("href").split("sort=")[1])
            rows = users_div.find("tbody").find_all("tr")
            for row in rows:
                columns = row.find_all("td")
                link = columns[-1].find("a").get("href")
                user_id = int(link.split("=")[-1])
                message_link = self._url + "/".join(link.split("/")[2:])
                details = {c: columns[head_columns.index(c)].text.strip().replace("  ", " ") for c in head_columns}
                users.append(User(id=user_id, details=details, message_link=message_link))
            pagination = parsed_html.body.find("div", id="users").find(class_="pagination")
            if pagination:
                next_page = pagination.find(class_="next_page")
                if next_page:
                    page += 1
                else:
                    page = None
            else:
                page = None

        return users

#This should work as an object API to connect with foodsoft and
#work with it.

from json import dumps
import logging
import requests
from bs4 import BeautifulSoup as bs

logging.basicConfig(level=logging.DEBUG)

class User:
    def __init__(self, id, name, e_mail, message_link=None, phone_number=None):
        self.id = id
        self.name = name
        self.e_mail = e_mail
        self.message_link = message_link
        self.phone_number = phone_number

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
            parsed_html = bs(self._get(userlist_url, self._default_header).content, 'html5lib')
            rows = parsed_html.body.find("div", id="users").find("tbody").find_all("tr")
            for row in rows:
                colums = row.find_all("td")
                link = colums[5].find("a").get("href")
                user_id = int(link.split("=")[-1])
                message_link = self._url + "/".join(link.split("/")[2:])
                users.append(User(id=user_id, name=colums[0].text.strip().replace("  ", " "), e_mail=colums[1].text.strip(), phone_number=colums[2].text.strip(), message_link=message_link))
            pagination = parsed_html.body.find("div", id="users").find(class_="pagination")
            if pagination:
                next_page = pagination.find(class_="next_page")
                if next_page:
                    page += 1
                else:
                    page = None
            else:
                page = None

        # for user in users:
        #     print(f"{user.id} - {user.name} - {user.e_mail} - {user.phone_number} - {user.message_link}")

        return users

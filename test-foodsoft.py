import json
from foodsoft import FSConnector

config_path = '_credentials/config.json'
def read_config():
    with open(config_path) as json_file:
        return json.load(json_file)

config = read_config()['foodsoft']
fsc = FSConnector(config['url'], config['user'], config['password'])

fsc.sendMailToRecipients([315], {"subject":"class-subject", "body":"Wie schauts mit Ümläuten aus?\n Und zeilenübrüche?\n\nHö€"})
fsc.logout()

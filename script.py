#!/usr/bin/env python3
import ethercalc
import json
import logging
import pprint

pp = pprint.PrettyPrinter(indent=4)

def read_config():
  with open('_credentials/config.json') as json_file:
    return json.load(json_file)

def load_ethercalc(config):
  return ethercalc.EtherCalc(config["host"]).export(config["page"])


def main():
  logging.basicConfig(level=logging.DEBUG)
  logging.debug("Enter Main()")
  config = read_config()
  logging.debug("remote host: " + config["host"] + " remote page: " + config["page"])
  pp.pprint(load_ethercalc(config))
  
if __name__== "__main__":
  main()


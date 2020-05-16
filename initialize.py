#!/usr/bin/env python3
import ethercalc
import json
import logging
import pprint
import os
import script

pp = pprint.PrettyPrinter(indent=4)
config = script.read_config()
language = None

def initialize(language):
    with open('locales/'+language+'/locales.json', encoding='utf-8') as json_file:
        locales = json.load(json_file)
    new_sheet_host = ethercalc.EtherCalc(config["host"])
    for i in range(5):
        no = i + 1
        new_sheet_host.command(config["page"], ["set A"+str(no+1)+" text t /"+config["page"]+"."+str(no)])
        new_sheet_host.command(config["page"], ["set B"+str(no+1)+" text t "+locales["sheet"+str(no)]])
        with open('locales/'+language+"/sheet"+str(no)+".txt", "r", encoding='utf-8') as text_file:
            sheet = text_file.read()
        print(sheet)
        new_sheet_host.update(sheet, format="socialcalc", id=config["page"]+"."+str(no))

def main():
    logging.basicConfig(level=logging.DEBUG)
    logging.debug("Enter Main()")

    default_sheet_languages = []
    folders = os.listdir('locales/')
    for folder in folders:
        if os.path.isfile("locales/"+folder+"/sheet1.txt"):
            default_sheet_languages.append(folder)

    if default_sheet_languages:
        if len(default_sheet_languages) > 1:
            print("You are about to initialize an empty sheet at "+config["host"]+"/="+config["page"]+". \nFound default sheet languages: "+script.semicolon_separated_list_from_python_list(any_list=default_sheet_languages)) # 
            language = input("To continue, please enter in which of the languages above you want the sheet to be: ")
            while language not in default_sheet_languages:
                language = input("Chosen language not found. Try again: ")
        else:
            language = default_sheet_languages[0]
        initialize(language=language)
    else:
        print("No locales with default sheets found.")


if __name__== "__main__":
    main()
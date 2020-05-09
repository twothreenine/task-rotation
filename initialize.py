#!/usr/bin/env python3
import ethercalc
import json
import logging
import pprint
import script

pp = pprint.PrettyPrinter(indent=4)
config = script.read_config()
language = None

with open('default_sheets.json') as json_file:
    default_sheets = json.load(json_file)

def test():
    # test_sheet = script.load_ethercalc(host=default_sheets[language]["host"], page=default_sheets[language]["page"])
    default_sheet_page = default_sheets[language]["page"]
    default_sheet_host = default_sheets[language]["host"]
    new_sheet_host = ethercalc.EtherCalc(config["host"])
    base_sheet = script.load_ethercalc(host=default_sheet_host, page=default_sheet_page)
    for i in range(5):
        new_sheet_host.command(config["page"], ["set A"+str(i+2)+" text t /"+config["page"]+"."+str(i+1)])
        new_sheet_host.command(config["page"], ["set B"+str(i+2)+" text t "+base_sheet[i+1][1]])
    notes_sheet = script.load_ethercalc(host=default_sheet_host, page=default_sheet_page, sheet=4, export_format="socialcalc")
    # pp.pprint(events_sheet)
    new_sheet_host.create(notes_sheet, format="socialcalc", id=config["page"]+".4")

    # pane row 3 (all tables)
    # insert formula for calender week + weekday

    # default_sheet_host.command(default_sheet_page+".1", ["copy A1:W3 formulas"])
    # new_sheet_host.command(config["page"]+".1", ["paste A1 formulas"])

def main():
    logging.basicConfig(level=logging.DEBUG)
    logging.debug("Enter Main()")

    global language
    if default_sheets:
        if len(default_sheets) > 1:
            default_sheets_str = ""
            print("You are about to initialize an empty sheet at "+config["host"]+"/="+config["page"]+". \nRegistered default sheet languages: "+script.dict_str(any_dict=default_sheets)) # 
            language = input("To continue, please enter in which of the languages above you want the sheet to be: ")
            while language not in default_sheets:
                language = input("Chosen language not registered. Try again: ")
        else:
            language = default_sheets[0]
        # TODO
        test()
    else:
        print("No default sheet languages registered.")

if __name__== "__main__":
    main()
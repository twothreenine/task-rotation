#!/usr/bin/env python3
import ethercalc
import json
import logging
import pprint
import script
import os

pp = pprint.PrettyPrinter(indent=4)

def export(host, page, sheets=[None,1,2,3,4,5], folder=None):
    if not folder:
        folder = page
    folder = "exported_sheets/" + folder
    for no in sheets:
        if no == "None":
            no = None
        sheet = script.load_ethercalc(host=host, page=page, sheet=no, export_format="socialcalc")
        if not no:
            sheet_no = "_base"
        else:
            sheet_no = str(no)
        if not os.path.exists(folder):
            os.makedirs(folder)
        file = open(folder+"/sheet"+sheet_no+".txt","w", encoding='utf-8')
        file.write(sheet)
        file.close()

def main():
    logging.basicConfig(level=logging.DEBUG)
    logging.debug("Enter Main()")

    host = input("Please enter host URL: ")
    page = input("Please enter page: ")

    export(host=host, page=page)
        


if __name__== "__main__":
    main()
#!/usr/bin/env python3
import ethercalc
import json
import logging
import pprint
import os
import script

pp = pprint.PrettyPrinter(indent=4)

calcs = script.get_calc_configs()
calc_names = []
for calc in calcs:
    calc_names.append(calc["name"])

def initialize(host, page, language, name, overwrite=False):
    with open('locales/'+language+'/locales.json', encoding='utf-8') as json_file:
        locales = json.load(json_file)
    new_calc_host = ethercalc.EtherCalc(host)
    for i in range(5):
        no = i + 1
        new_calc_host.command(page, ["set A"+str(no+1)+" text t /"+page+"."+str(no)])
        new_calc_host.command(page, ["set B"+str(no+1)+" text t "+locales["sheet"+str(no)]])
        # sheet = script.load_ethercalc(host=host, page="w2jjmp1soy3s", sheet=no, export_format="socialcalc")
        with open('locales/'+language+"/sheet"+str(no)+".txt", "r", encoding='utf-8') as text_file:
            sheet = text_file.read().encode("utf-8")
        new_calc_host.update(sheet, format="socialcalc", id=page+"."+str(no))
    new_calc_host.command(page+".5", ["set C6 text t "+name])

    available_locales = []
    folders = os.listdir('locales/')
    for folder in folders:
        if os.path.isfile("locales/"+folder+"/locales.json"):
            available_locales.append(folder)
    new_calc_host.command(page+".5", ["set D5 text t "+script.semicolon_separated_list_from_python_list(any_list=available_locales)])

    if not os.path.exists("_credentials/calc_urls"):
        os.makedirs("_credentials/calc_urls")
    data = {'host': host, 'page': page, 'name': name}

    name_no = ""
    if name in calc_names and not overwrite:
        name_no = 2
        while name+"_"+str(name_no) in calc_names:
            name_no += 1
        name_no = "_" + str(name_no)
    file_name = name + name_no

    with open("_credentials/calc_urls/"+file_name+".json", 'w') as outfile:
        json.dump(data, outfile)

def main():
    logging.basicConfig(level=logging.DEBUG)
    logging.debug("Enter Main()")

    default_sheet_languages = []
    folders = os.listdir('locales/')
    for folder in folders:
        if os.path.isfile("locales/"+folder+"/sheet1.txt"):
            default_sheet_languages.append(folder)

    if default_sheet_languages:
        host = str(input("Please enter the host URL for the new sheet: "))
        page = str(input("Please enter the page ID for the new sheet: "))
        name = str(input("Please enter a name for the new sheet / task group: "))
        overwrite = False
        if name in calc_names:
            overwrite_yn = input(name+" already exists in this environment. Overwrite? (Y/N) ")
            while not script.is_yn(overwrite_yn):
                overwrite_yn = input("Insert Y to overwrite or N to not overwrite: ")
            if overwrite_yn == "Y" or overwrite_yn == "y":
                overwrite = True

        if len(default_sheet_languages) > 1:
            print("Found default sheet languages: "+script.semicolon_separated_list_from_python_list(any_list=default_sheet_languages)) # 
            language = input("Please enter in which of the languages above you want the sheet to be: ")
            while language not in default_sheet_languages:
                language = input("Chosen language not found. Try again: ")
        else:
            language = default_sheet_languages[0]
        initialize(host=host, page=page, language=language, name=name, overwrite=overwrite)
        print("Taskrotation calc initialized at "+host+"/="+page)
    else:
        print("No locales with default sheets found.")


if __name__== "__main__":
    main()
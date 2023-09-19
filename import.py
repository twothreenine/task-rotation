import ethercalc
import json
import logging
import pprint
import os
import script

def main():
    logging.basicConfig(level=logging.DEBUG)
    logging.debug("Enter Main()")

    local_file = False
    local_file_yn = input("You can either import a local socialcalc file or copy a socialcalc sheet from the web. Enter Y for local file or N for copying: ")
    while not script.is_yn(local_file_yn):
        local_file_yn = input("Enter Y for local file or N for copying: ")
    if local_file_yn == "Y" or local_file_yn == "y":
        local_file = True
        path = str(input("Paste path of local socialcalc file: "))
        path = path.replace("\\", "/")
        with open(path, "r", encoding='utf-8') as text_file:
            sheet = text_file.read().encode("utf-8")
    else:
        source_host = str(input("Please enter the host URL of the sheet you want to copy: "))
        source_page = str(input("Please enter the page ID for the sheet you want to copy (single sheet without '=' in front): "))
        print("Trying to copy sheet from " + source_host + "/" + source_page)
        sheet = script.load_ethercalc(host=source_host, page=source_page, export_format="socialcalc").encode("utf-8")

    write = False
    while not write:
        host = str(input("Please enter the new host URL for the sheet: "))
        page = str(input("Please enter the new page ID for the sheet (open the sheet once before proceeding): "))
        existing_sheet = script.load_ethercalc(host=host, page=page, export_format="socialcalc")
        if "version:1.5\nsheet:" not in existing_sheet:
            overwrite = str(input("The sheet you want to replace doesn't seem to be empty! Are you sure you want to overwrite it? (Y/N) "))
            while not script.is_yn(overwrite):
                overwrite = str(input("Enter Y to overwrite it or N to choose a different page ID: "))
            if overwrite == "Y" or overwrite == "y":
                write = True
        else:
            write = True

    new_calc_host = ethercalc.EtherCalc(host)
    new_calc_host.update(sheet, format="socialcalc", id=page)


if __name__== "__main__":
    main()

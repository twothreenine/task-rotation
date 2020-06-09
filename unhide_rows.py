import ethercalc
import logging
import script

calc_names = script.list_calc_url_files()
if calc_names:
    if len(calc_names) == 1:
        calc_name = calc_names[0]
    else:
        print("Calcs found: "+script.semicolon_separated_list_from_python_list(any_list=calc_names))
        calc_name = input("Enter the name of the calc (see list above) for which you want to unhide rows: ")
        while calc_name not in calc_names:
            calc_name = input("No calc with this name found. Try again: ")

    script.load_calc_data(file_name=calc_name)
    settings_list = script.load_ethercalc(sheet=5)
    header_lines = script.find_header_lines(settings_list=settings_list)
    print("header lines = "+str(header_lines))

    rows = input("Up to which row of "+calc_name+"'s events table do you want to unhide? ")

    e = ethercalc.EtherCalc(script.calc["host"])
    e.command(script.calc["page"]+".1", ["set "+str(header_lines+1)+":"+str(rows)+" hide"])
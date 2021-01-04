import ethercalc
import logging
import script

calc_configs = script.get_calc_configs()
if calc_configs:
    if len(calc_configs) == 1:
        calc_config = calc_configs[0]
    else:
        calc_names = []
        for calc_config in calc_configs:
            calc_names.append(calc_config['name'])
        print("Calcs found: "+script.semicolon_separated_list_from_python_list(any_list=calc_names))
        script.calc['name'] = input("Enter the name of the calc (see list above) for which you want to unhide rows: ")
        while script.calc['name'] not in calc_names:
            script.calc['name'] = input("No calc with this name found. Try again: ")

    script.set_calc_data(config=calc_config)
    settings_list = script.load_ethercalc(sheet=5)
    header_lines = script.find_header_lines(settings_list=settings_list)
    print("header lines = "+str(header_lines))

    rows = input("Up to which row of "+script.calc['name']+"'s events table do you want to unhide? ")

    e = ethercalc.EtherCalc(script.calc["host"])
    e.command(script.calc["page"]+".1", ["set "+str(header_lines+1)+":"+str(rows)+" hide"])
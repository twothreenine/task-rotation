import ethercalc
import logging
import script

config = script.read_config()

rows = input("Up to which row do you want to unhide? ")

e = ethercalc.EtherCalc(config["host"])
e_page = config["page"]+".1"
e.command(e_page, ["set 3:"+str(rows)+" hide"])
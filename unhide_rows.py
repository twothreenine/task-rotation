import ethercalc
import logging
import script

config = script.read_config()

e = ethercalc.EtherCalc(config["host"])
e_page = config["page"]+".1"
e.command(e_page, ["set 3:42 hide"])
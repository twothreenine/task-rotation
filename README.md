# task-rotation

Python script for automatic assignment of recurring tasks within a group

[Details (German)](https://github.com/twothreenine/task-rotation/blob/master/manuals/manual_de.md)

## Requirements:

 python v3.6 or higher
 
 pip install Babel
 
 pip install ethercalc-python

*replace ethercalc-python by following version: https://github.com/twothreenine/ethercalc-python*

Beautiful Soup

Selenium

Webdriver Manager

## execute

for a single run: 
 python script.py

as service:
 python script.py --service

## example sheet

https://calc.foodcoops.at/=taskrotation0-2_en

## Docker

  docker build -t <image-name> .
  docker run --env-file env.list <image-name>

## Configuration
For configuration environment variables are used. The following list shows the available variables.

Note that all of theses variables needs to be set, otherwise the script will not work!
* TR_CALC_HOST=<url to ethercalc host server (use ';' as seperator for multiple instances)>
* TR_CALC_PAGE=<name of your sheet, without equals (use ';' as seperator for multiple instances)>
* TR_CALC_NAME=<name for your sheet human readable (use ';' as seperator for multiple instances)>
* TR_FOODSOFT_URL=<url to your foodsoft instance>
* TR_FOODSOFT_USER=<foodsoft-user>
* TR_FOODSOFT_PASS=<foodsoft-password>
* TR_LOG_MAIL_SERVER=<server name of smtp server>
* TR_LOG_MAIL_PORT=<smpt port, e.g.: for STARTTLS: 587>  
* TR_LOG_MAIL_USER=<login user> 
* TR_LOG_MAIL_PASS=<login password>
* TR_LOG_MAIL_SENDER=<sender name/mail adress>
* TR_LOG_MAIL_SUBJECT_PREFIX=<prefix of each log mail>
* TR_LOG_MAIL_SUBSCRIBORS=<mail-adress:LOG-LEVEL;...>, where LEVEL = {INFO:ERROR}



for local use in Windows 10:
* open system settings
* search for "variable"
* select "edit system environment variables" or "edit environment variables for this account" respectively (or similar)
* set variables manually (only TR_CALC_HOST, TR_CALC_PAGE, TR_CALC_NAME necessary, foodsoft optionally)

[more infos](https://superuser.com/questions/949560/how-do-i-set-system-environment-variables-in-windows-10)

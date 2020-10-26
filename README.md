# task-rotation

Python script for automatic assignment of recurring tasks within a group

[Details (German)](https://github.com/twothreenine/task-rotation/blob/master/manuals/manual_de.md)

## Requirements:

 python v3.x
 
 pip install ethercalc-python
 
 pip install Babel

## execute

 python script.py

## example sheet

https://ethercalc.net/=taskrotation0-1

## Docker

  docker build -t <image-name> .
  docker run --env-file env.list <image-name>

## Configuration
For configurations environment variables are used. The following list shows the available variables.
Note that all of theses variables needs to be set, otherwise the script will not work! Multiple instances can be handled, by using a ';' as seperator.
* TR_FOODSOFT_URL=<url to your foodsoft instance>
* TR_FOODSOFT_USER=<foodsoft-user>
* TR_FOODSOFT_PASS=<foodsoft-password>
* TR_CALC_HOST=<url to ethercalc instance>
* TR_CALC_PAGE=<name of your sheet, without equals>
* TR_CALC_NAME=<name for your sheet human readable>

in Windows 10 PowerShell:
$env:TR_foodsoft_url='...'
etc.
more infos: https://superuser.com/questions/949560/how-do-i-set-system-environment-variables-in-windows-10

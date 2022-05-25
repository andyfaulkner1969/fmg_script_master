# README

This is a project to create a full functioning FortiManager CLI Script tool.

Created by Andy Faulkner afaulkner@fortinet.com evil@evilbast.com

This script will allow you to do the following..

Upload scripts to and FMG ADOM
Create a script and upload to FMG on the fly
Run a script on a device in an ADOM
Run a script on all devcies in an ADOM
Can delete scripts in an ADOM.
Can read scripts in an ADOM.
It also logs the script history both to screen and log file.

You will need to have both the script and the script_master.ini file.
You will need to configure the script_master.ini file with your FMG settings.

Files:

cli_ex_config_port3 - Example CLI script
cli_ex_get_system_get_interface - Example CLI script
config_creator.py - Python script that will generate the script_master.ini  Not needed unless you are going to develop your own version.
fmg_script_master_v1.2.py - Primary script - must configure the script_master.ini in order to work.  
script_master.ini - Config file, FortiManager IP address, username, password (if you desire), debug settings.

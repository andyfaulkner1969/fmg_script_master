#!/usr/bin/env python3

""""
FortiManager Script Executor

This program will execute scripts on devices that reside on an FortiManager

by:
 ________         ____     _ __  ___           __              __
/_  __/ /  ___   / __/  __(_) / / _ )___ ____ / /____ ________/ /
 / / / _ \/ -_) / _/| |/ / / / / _  / _ `(_-</ __/ _ `/ __/ _  /
/_/ /_//_/\__/ /___/|___/_/_/ /____/\_,_/___/\__/\_,_/_/  \_,_/

afaulkner@fortinet.com / evil@evilbast.com

"""

#  Version 1.2 - Features added - Ablility to run a script on all devices in an ADOM, 
#   When running a script on all devices in an ADOM you can now log the script history
#   to file <device_name>_script_history.log.

import requests
import json
import urllib3
import time
import logging
import os

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Set flag to DEBUG to get full logging.
debug_flag = logging.INFO
logging_file = 'fmg_script.log'
logging.basicConfig(level=debug_flag, format='%(asctime)s:%(levelname)s:%(message)s')
# To log to file comment the line above and uncomment the line below.
# logging.basicConfig(filename=logging_file,level=logging.DEBUG,format='%(asctime)s:%(levelname)s:%(message)s')

fmg_ip = "FMG IP ADDRESS"
fmg_user = "FMG api user"
fmg_passwd = "FMG api user password"
# The path variable below is the search directory to where preconfigured CLI scripts reside.
# Default is . the same directory as where the script resides.  Change if different.
path = "."

# This is an exclusion list of default ADOMs that are installed in FMG by default.  Adding to this list
# will remove any ADOM from adom choice.
adom_exclude = ["FortiAnalyzer", "FortiAuthenticator", "FortiCache", "FortiCarrier", "FortiClient",
                "FortiDDoS", "FortiDeceptor", "FortiFirewall", "FortiFirewallCarrier", "FortiMail",
                "FortiManager", "FortiNAC", "FortiProxy", "FortiSandbox", "FortiWeb", "Unmanaged_Devices",
                "rootp", "others", "Syslog"]
# STATIC global variables do not change
sid = ""
adom_choice = ""
device_choice = ""
script_choice = ""
task_num = ""
percent_dn = ""
url_base = "https://" + fmg_ip + "/jsonrpc"

def fmg_login():
    logging.debug("**** Start of the fmg_login function ****")
    # Logging into FMG and getting session id "sid"
    global sid
    global url_base
    client = requests.session()

    payload = {
        "id": 1,
        "method": "exec",
        "params": [
            {
                "data": {
                    "passwd": fmg_passwd,
                    "user": fmg_user,
                },
                "url": "/sys/login/user"
            }
        ]
    }
    r = client.post(url_base, json=payload, verify=False)
    # Retrieve session id. Add to HTTP header for future messages parsed_json = json.loads(r.text)
    parsed_json = json.loads(r.text)
    logging.debug("Response from FMG: " + str(parsed_json))
    try:
        sid = parsed_json['session']
        headers = {'session': sid}
    except:
        print("Error happened attempting to log in to FMG")
        logging.debug("Issue with logging in to FMG check IP/FQDN or user/password")
    return (sid)

def fmg_logout():
    logging.debug("**** Start of the fmg_logout function ****")
    # Logging out of FMG
    global sid
    global url_base
    client = requests.session()
    payload = {
        "id": 1,
        "method": "exec",
        "params": [
            {
                "url": "/sys/logout"
            }
        ],
        "session": sid
    }
    r = client.post(url_base, json=payload, verify=False)
    parsed_json = json.loads(r.text)
    logging.info("Logging out of FMG")
    logging.debug("Response from FMG: " + str(parsed_json))

def fmg_adom_list():
    logging.debug("**** Start of the fmg_adom_list function ****")
    # Getting FMG adom list
    global sid
    global adom_choice
    global url_base
    adom_list_temp = []
    client = requests.session()
    payload = {
        "method": "get",
        "params": [
            {
                "fields": ["name", "desc"],
                "loadsub": 0,
                "url": "/dvmdb/adom"
            }
        ],
        "session": sid,
        "id": 1
    }
    r = client.post(url_base, json=payload, verify=False)
    parsed_json = json.loads(r.text)
    logging.debug(parsed_json)
    logging.debug("Getting list of ADOMs")
    logging.debug("Response from FMG: " + str(parsed_json))
    adom_ct = len(parsed_json["result"][0]["data"])
    logging.debug("Adom count is " + str(adom_ct))
    count = 0
    adom_list = []
    while count < adom_ct:
        adom_name = parsed_json["result"][0]["data"][count]["name"]
        adom_list_temp.append(adom_name)
        count = count + 1
    logging.debug("Here is a list of ALL the FMG adom names: " + str(adom_list_temp))
    index = 1
    # Removing unwanted ADOMs from the list
    # ADOMs from list.
    for item in adom_list_temp:
        # print(item)
        if item in adom_exclude:
            pass
        else:
            adom_list.append(item)
    logging.debug("Here is a list of FINAL FMG adom names: " + str(adom_list))
    # Making a dictionary with adom names and numbers
    num_choice = {}
    for index, value in enumerate(adom_list, 1):
        print("{}. {}".format(index, value))
        num_choice.update({index: value})
    # Getting choice
    choice = int(input("Enter the number :"))
    if choice in num_choice:
        print("ADOM is set to " + num_choice[choice])
        adom_choice = num_choice[choice]
    else:
        logging.info("Could not find the number of ADOM that was picked")
        logging.info("exiting the script")
        exit()
    return (adom_choice)

def device_list():
    logging.debug("**** Start of the device_list function ****")
    # Getting device list from picked ADOM
    global sid
    global adom_choice
    global device_choice
    global url_base
    client = requests.session()

    payload = {
        "method": "get",
        "params": [
            {
                "fields": ["name", "sn"],
                "loadsub": 0,
                "url": "/dvmdb/adom/" + adom_choice + "/device"
            }
        ],
        "session": sid,
        "id": 1
    }

    r = client.post(url_base, json=payload, verify=False)
    parsed_json = json.loads(r.text)
    logging.debug("Here is the parsed json from device_list : " + str(parsed_json))
    device_ct = len(parsed_json["result"][0]["data"])
    logging.debug(str("Count of devices in ADOM : " + str(device_ct)))
    print(parsed_json["result"][0]["data"][0]["name"])
    count = 0
    device_list = []
    while count < device_ct:
        device_name = parsed_json["result"][0]["data"][count]["name"]
        device_list.append(device_name)
        count = count + 1
    logging.debug("Here is a list of the devices in the " + str(adom_choice) + " : " + str(device_list))
    device_list.append("ALL DEVICES")
    # Making a dictionary with device names and numbers
    index = 1
    num_choice = {}
    for index, value in enumerate(device_list, 1):
        print("{}. {}".format(index, value))
        num_choice.update({index: value})
    # Getting choice
    choice = int(input("Enter the number in the list: "))
    if choice in num_choice:
        print("Device is set to " + num_choice[choice])
        device_choice = num_choice[choice]
        logging.debug("User choose : " + str(device_choice))
    if device_choice == "ALL DEVICES":
        logging.debug("Returning device list.")
        return device_list
    if isinstance(device_choice, str):
        logging.debug("Returning single device.")
        return device_choice
    else:
        logging.info("Could not find the device that was picked.")
        logging.info("exiting the script!  Come on man this is simple stuff!")
        exit()
    return (device_choice)

def get_script_list():
    # Getting list of scripts from ADOM.
    logging.debug("**** Start of the get_script_list function ****")
    global sid
    global adom_choice
    global device_choice
    global script_choice
    global url_base
    client = requests.session()

    payload = {
        "method": "get",
        "params": [
            {
                "fields": ["name", "desc"],
                "loadsub": 0,
                "url": "/dvmdb/adom/" + adom_choice + "/script"
            }
        ],
        "session": sid,
        "id": 1
    }

    r = client.post(url_base, json=payload, verify=False)
    parsed_json = json.loads(r.text)
    logging.debug("Here is the parsed json of the script list : " + str(parsed_json))
    script_ct = len(parsed_json["result"][0]["data"])
    logging.debug("Number of Scripts in ADOM : " + str(script_ct))
    script_list = []
    count = 0
    print("*** List of scripts in ADOM ***")
    while count < script_ct:
        script_list.append(parsed_json["result"][0]["data"][count]["name"])
        count = count + 1
    # Create dict for script list
    index = 1
    num_choice = {}
    for index, value in enumerate(script_list, 1):
        print("{}. {}".format(index, value))
        num_choice.update({index: value})
    # Getting choice
    choice = int(input("Enter the number :"))
    if choice in num_choice:
        script_choice = num_choice[choice]
        logging.debug("Script choice is :" + script_choice)
    else:
        logging.info("Could not find the script that was picked.")
        logging.info("exiting the script!  Come on man this is simple stuff!")
        exit()
    logging.debug("The script that was picked is : " + str(script_choice))
    return (script_choice)

def execute_script():
    # Executing script on piced ADOM, Device and script choices.
    logging.debug("**** Start of the execute_script function ****")
    global sid
    global adom_choice
    global device_choice
    global script_choice
    global url_base
    global task_num
    client = requests.session()
    payload = {
        "method": "exec",
        "params": [
            {
                "data": {
                    "adom": adom_choice,
                    "scope": [
                        {
                            "name": device_choice,
                            "vdom": "root"
                        }
                    ],
                    "script": script_choice
                },
                "url": "/dvmdb/adom/" + adom_choice + "/script/execute"
            }
        ],
        "session": sid,
        "id": 1
    }
    r = client.post(url_base, json=payload, verify=False)
    parsed_json = json.loads(r.text)
    logging.debug("Here is the parsed json of execute script: " + str(parsed_json))
    task_num = parsed_json["result"][0]["data"]["task"]
    logging.debug("Here is the task number " + str(task_num))
    return (task_num)

def task_ck():
    # Checking on the task, once it gets to 100% done.
    logging.debug("**** Start of the task_ck function ****")
    global sid
    global task_num
    global url_base
    global percent_dn
    client = requests.session()
    payload = {
        "method": "get",
        "params": [
            {
                "url": "/task/task/" + str(task_num)

            }
        ],
        "session": sid,
        "id": 1
    }

    r = client.post(url_base, json=payload, verify=False)
    parsed_json = json.loads(r.text)
    logging.debug("This is the parsed json from checking task" + str(parsed_json))
    percent_dn = parsed_json['result'][0]['data']['percent']
    return percent_dn

def get_script_history():
    # Go get the result of the script running.
    logging.debug("**** Start of the get_script_histor function ****")
    global sid
    global adom_choice
    global device_choice
    global script_choice
    global url_base
    global task_num
    client = requests.session()
    payload = {
        "method": "get",
        "params": [
            {
                "url": "/dvmdb/adom/" + adom_choice + "/script/log/latest/device/" + device_choice
            }
        ],
        "session": sid,
        "id": 1
    }

    r = client.post(url_base, json=payload, verify=False)
    parsed_json = json.loads(r.text)
    logging.debug("Here is the parsed json of execute script: " + str(parsed_json))
    script_result = parsed_json["result"][0]["data"]["content"]
    print(script_result)
    return script_result

def get_file_choice():
    global path
    file_choice = ""
    logging.debug("**** Start of the get_file_choice function ****")
    #  Get a list of files
    file_list = []
    for x in os.listdir(path):
        if x.startswith("."):
            pass
        else:
            file_list.append(x)
    file_list_count = len(file_list)
    if file_list_count == 0:
        logging.info("No files found")
        exit()
    file_list_choice = {}

    for index, value in enumerate(file_list, 1):
        print("{}. {}".format(index, value))
        file_list_choice.update({index: value})

    choice = int(input("Enter the number for the file you want to upload: "))

    if choice in file_list_choice:
        file_choice = file_list_choice[choice]
    else:
        print("Not Found, exiting the script")
        exit()
    return file_choice

def file_to_string_parse(script_file):
    logging.debug("**** Start of the file_to_string_parse function ****")
    logging.debug("Here is the script file that was passed into this function: " + script_file)
    script_line_list = []
    script_txt = ""
    logging.debug("Opening CLI file")
    f = open(script_file, 'r')
    lines = f.readlines()
    for item in lines:
        script_line_list.append(item)
    for item in script_line_list:
        # script_txt += item + "\n"
        script_txt += item
    logging.debug("Closing CLI file.")
    f.close()
    return script_txt

def script_upload(script_name, script_desc, script):
    logging.debug("**** Start of the script upload function ****")
    logging.debug("The following items were passed into this function  :")
    logging.debug("Script Name: " + script_name)
    logging.debug("Script Description : " + script_desc)
    logging.debug("Script Content : " + script)
    logging.info("Uploading script to FMG")
    # Logging into FMG and getting session id "sid"
    global sid
    global url_base
    global adom_choice
    global path
    client = requests.session()
    payload = {
        "method": "add",
        "params": [
            {
                "data": [
                    {
                        "content": script,
                        "desc": script_desc,
                        "name": script_name,
                        "target": "remote_device",
                        "type": "cli"
                    }
                ],
                "url": "/dvmdb/adom/" + adom_choice + "/script"
            }
        ],
        "session": sid,
        "id": 1
    }
    r = client.post(url_base, json=payload, verify=False)
    # Retrieve session id. Add to HTTP header for future messages parsed_json = json.loads(r.text)
    parsed_json = json.loads(r.text)
    logging.debug("Response from FMG: " + str(parsed_json))
    if parsed_json['result'][0]['status']['code'] == 0:
        logging.info("Script uploaded.")
    else:
        logging.info("Something went wrong, I suggest you run DEBUG.")

def script_cmdl():
    logging.debug("**** Start of the script_cmdl function ****")
    print("Enter the CLI commands for your script.  Crtl-D or Crtl-Z (for windows) to save it.")
    script_list = []
    script_txt = ""
    while True:
        try:
            line = input()
        except EOFError:
            print("All text has been entered.")
            break
        script_list.append(line)
    for item in script_list:
        script_txt += item + "\n"
    return script_txt

def get_script_txt():
    global sid
    global adom_choice
    global script_choice
    logging.debug("**** Start of the get_script_txt function ****")
    client = requests.session()
    script = {
        "method": "get",
        "params": [
            {
                "loadsub": 0,
                "url": "/dvmdb/adom/" + adom_choice  + "/script/" + script_choice
            }
        ],
        "session": sid,
        "id": 1
    }
    
    r = client.post(url_base, json=script, verify=False)
    parsed_json = json.loads(r.text)
    logging.debug(parsed_json)
    script_txt = parsed_json['result'][0]['data']['content']
    print("Here is the script " + script_choice)
    print("-----------------------------------")
    print(script_txt)
    print("-----------------------------------")
    if parsed_json['result'][0]['status']['code'] == 0:
        logging.info("Script " + script_choice + " received from " + adom_choice)
    else:
        logging.info("Something went wrong, I suggest you run DEBUG.")
        
def script_delete():
    global sid
    global adom_choice
    global script_choice
    logging.debug("**** Start of the script_delet function ****")
    client = requests.session()
    script = {
        "method": "delete",
        "params": [
            {
                "loadsub": 0,
                "url": "/dvmdb/adom/" + adom_choice  + "/script/" + script_choice
            }
        ],
        "session": sid,
        "id": 1
    }
    
    r = client.post(url_base, json=script, verify=False)
    parsed_json = json.loads(r.text)
    logging.debug(parsed_json)
    if parsed_json['result'][0]['status']['code'] == 0:
        logging.info("Deleted script " + script_choice + " from " + adom_choice)
    else:
        logging.info("Something went wrong, I suggest you run DEBUG.")
    
def script_direction():
    # This is where we decide which direction the script goes upload or execute.
    logging.debug("Start of script_direction function.")
    direction_choice = ""
    choices = ['Upload a new script to FMG', 'Run a script on a device via FMG', 'Print out existing script.', 'Delete a script.']
    num_choice = {}
    for index, value in enumerate(choices, 1):
        print("{}. {}".format(index, value))
        num_choice.update({index: value})
    # Getting choice
    choice = int(input("Enter the number :"))
    if choice in num_choice:
        print("You choose : " + num_choice[choice])
        return choice
    else:
        logging.info("Could not find the number that was picked, I didn't think it was that hard a choice.")
        logging.info("Giving up and exiting the script.")
        exit()
        
def direction_1():
    global device_choice
    logging.debug("start of direciton_1 function")
    logging.debug("Choice was made to upload a script.")
    fmg_login()
    fmg_adom_list()
    script_name = input("Enter the name of your script: ")
    script_desc = input("Enter a description of your script: ")
    file_choice = input("Do you want to upload preconfigured file? y/n :")
    if file_choice == "y":
        script_file = get_file_choice()
        script = file_to_string_parse(script_file)
        script_upload(script_name, script_desc, script)
    if file_choice == "n":
        script = script_cmdl()
        script_upload(script_name, script_desc, script)
    time.sleep(1)
    fmg_logout()
    
def direction_2():
    global device_choice
    logging.debug("start of direciton_2 function")
    logging.debug("Choice was made to execute a script on a device.")
    fmg_login()
    fmg_adom_list()
    run_on_dev = device_list()
    # Here we check what was returned from the device_list choice.  If a single device it will be a stirng.
    # if it is a python list it will be a list of devices and we go into a loop.
    if isinstance(run_on_dev, str):
        get_script_list()
        print("The adom is : " + adom_choice + " - The device name is : " + device_choice + " - The script is : " + script_choice)
        execute_script()
        task_ck()
        while 100 > int(percent_dn):
            task_ck()
            print("Task is " + str(percent_dn) + "% done.")
            time.sleep(5)
        get_script_history()
        fmg_logout()
    if isinstance(run_on_dev, list):
        count = len(run_on_dev)
        count_up = 0
        get_script_list()
        log_to_file = input("Would you like to log the script history to file? (y/n) :")
        while count_up <= count:
            device_choice = run_on_dev[count_up]
            logging.debug("Current device choice from loop is " + device_choice)
            # NOTE: ALL DEVICES should always be the last choice in the list, once that is reached it leaves test.
            if device_choice != "ALL DEVICES":
                print("The adom is : " + adom_choice + " - The device name is : " + device_choice + " - The script is : " + script_choice)
                execute_script()
                task_ck()
                # Checking the status of the task on FMG.
                while 100 > int(percent_dn):
                    task_ck()
                    print("Task on " + str(device_choice) + " is " + str(percent_dn) + "% done.")
                    time.sleep(5)
                if log_to_file == "y":
                    logging.debug("Script logging set to file")
                    f = open(device_choice + "_script_history.log", 'w')
                    f.write(str(get_script_history()))
                    f.close()
                if logging_file =="n":
                    logging.debug("NO script logging to file.")
                    get_script_history()
                #time.sleep(5)  # Needed if bypassing task and script history otherwise will overrun the FMG.
                count_up = count_up + 1
                #exit()
            else:
                fmg_logout()
                exit()
        exit()
                
def direction_3():
    logging.debug("start of direciton_3 function")
    fmg_login()
    fmg_adom_list()
    get_script_list()
    get_script_txt()
    fmg_logout()
    
def direction_4():
    logging.debug("start of direciton_4 function")
    fmg_login()
    fmg_adom_list()
    get_script_list()
    script_delete()
    fmg_logout()
    
def main():
    global device_choice
    logging.debug("**** Start of the __main__ function ****")
    print("----------------------------------------------------")
    print("**** Welcome to FortiManager Script Master ****")
    print("              Use this with caution!  ")
    print("-----------------------------------------------------")
    direction = script_direction()
    if direction == 1:
        direction_1()
    if direction == 2:
        direction_2()
    if direction == 3:
        direction_3()
    if direction == 4:
        direction_4()

if __name__ == "__main__":
    main()
    
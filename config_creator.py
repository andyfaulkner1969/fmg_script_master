from configparser import ConfigParser

config = ConfigParser()

config['settings'] = {
    'fmg_ip' : '192.168.75.201',
    'fmg_user': 'api-user',
    'fmg_passwd':'CHANGE_ME'
}

config['debug'] = {
    'debug':'False'
}

config['directory'] = {
    'path':'./'
}

with open ('script_master.ini','w') as f:
    config.write(f)
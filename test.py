from termcolor import cprint
import json
import requests
from datetime import datetime
from random import randint

def getInventory(steamid):
    global count
    cprint(f"Accessing inventory of {steamid}", 'yellow', attrs=['bold'])
    data = requests.get(f'https://steamcommunity.com/inventory/{steamid}/730/2?l=english&count=5000')
    print(data)
    if data.status_code == 200: cprint(f"Inventory {steamid} loaded", 'green', attrs=['bold'])
    elif data.status_code == 429:
        cprint("Too many requests", 'red', attrs=['bold'])
        cprint(f"Exiting after {count} requests", 'red', attrs=['bold'])
        exit()
        return
    elif data.status_code == 404:
        cprint(f"Inventory of {steamid} not found", 'red', attrs=['bold'])
        return
    elif data.status_code == 500:
        cprint(f"Inventory of {steamid} is private", 'red', attrs=['bold'])
        return
    else:
        cprint(f"Inventory of {steamid} not loaded", 'red', attrs=['bold'])
        return
    json_data = json.loads(data.text)
    assets = json_data['assets']
    descriptions = json_data['descriptions']
    items = {}
    for asset in assets:
        id = asset['classid']
        if items.get(id) is None:
            items[id] = 1
        else:
            items[id] += 1
    inventory = {}
    for description in descriptions:
        id = description['classid']
        name = description['name']
        inventory[name] = items[id]
    count += 1
    return inventory

count = 0
interval = 5*60 # seconds
random_interval = 2*60 # seconds
before = datetime.now()
inventory = getInventory('76561198271959114')
INTERVAL = interval + randint(-random_interval, random_interval)
cprint(f"Next request in {INTERVAL} seconds", 'yellow', attrs=['bold'])
while 1:
    now = datetime.now()
    if (now - before).seconds >= INTERVAL:
        inventory = getInventory('76561198271959114')
        before = now
        INTERVAL = interval + randint(-random_interval, random_interval)
        cprint(f"Next request in {INTERVAL} seconds", 'yellow', attrs=['bold'])
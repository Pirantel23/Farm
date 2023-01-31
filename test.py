from termcolor import cprint
import json
import requests
from datetime import datetime
from random import randint
from colorama import just_fix_windows_console

def get_inventory(steamid, drops_only):
    cprint(f"Accessing inventory of {steamid}", 'yellow', attrs=['bold'])
    data = requests.get(f'https://steamcommunity.com/inventory/{steamid}/730/2?l=english&count=5000')
    
    print(data)
    if data.status_code == 200: cprint(f"Inventory {steamid} loaded", 'green', attrs=['bold'])
    elif data.status_code == 429:
        cprint("Too many requests", 'red', attrs=['bold'])
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
    f = open(f"{steamid}.json", "w")
    f.write(data.text)
    f.close()
    json_data = json.loads(data.text)
    inventory_count = json_data['total_inventory_count']
    if inventory_count == 0:
        cprint(f"Inventory of {steamid} is empty", 'red', attrs=['bold'])
        return
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
    if drops_only:
        drops = list(Drops.keys())
        for item in list(inventory.keys()):
            for drop in drops:
                if drop.lower()==item.lower():
                    break
            else:
                del inventory[item]
    return inventory

Drops = {"Fracture Case": r"Fracture%20Case",
         "Dreams and Nightmares Case": r"Dreams%20%26%20Nightmares%20Case",
         "Recoil Case": r"Recoil%20Case",
         "Clutch Case": r"Clutch%20Case",
         "Snakebite Case": r"Snakebite%20Case",
         "Operation Phoenix Weapon Case": r"Operation%20Phoenix%20Weapon%20Case",
         "Huntsman Weapon Case": r"Huntsman%20Weapon%20Case",
         "CS:GO Weapon Case": r"CS%3AGO%20Weapon%20Case",
         "Operation Bravo Case": r"Operation%20Bravo%20Case",
         "Spectrum Case": r"Spectrum%20Case",
         "Sticker Capsule": r"Sticker%20Capsule",
         "Danger Zone Case": r"Danger%20Zone%20Case",
         "Chroma 2 Case": r"Chroma%202%20Case",
         "Operation Wildfire Case": r"Operation%20Wildfire%20Case",
         "Spectrum 2 Case": r"Spectrum%202%20Case",
         "Chroma Case": r"Chroma%20Case",
         "Community Sticker Capsule 1": r"Community%20Sticker%20Capsule%201",
         "Winter Offensive Weapon Case": r"Winter%20Offensive%20Weapon%20Case",
         "Sticker Capsule 2": r"Sticker%20Capsule%202",
         "Prisma Case": r"Prisma%20Case",
         "Horizon Case": r"Horizon%20Case",
         "Falchion Case": r"Falchion%20Case",
         "Operation Vanguard Weapon Case": r"Operation%20Vanguard%20Weapon%20Case",
         "Gamma Case": r"Gamma%20Case",
         "Prisma 2 Case": r"Prisma%202%20Case",
         "Shadow Case": r"Shadow%20Case",
         "Glove Case": r"Glove%20Case",
         "Revolver Case": r"Revolver%20Case",
         "Operation Hydra Case": r"Operation%20Hydra%20Case",
         "CS20 Case": r"CS20%20Case",
         "Operation Breakout Weapon Case": r"Operation%20Breakout%20Weapon%20Case",
         "CS:GO Weapon Case 2": r"CS%3AGO%20Weapon%20Case%202",
         "CS:GO Weapon Case 3": r"CS%3AGO%20Weapon%20Case%203",
         "Gamma 2 Case": r"Gamma%202%20Case",
         "Chroma 3 Case": r"Chroma%203%20Case",
        }

just_fix_windows_console()
ACCOUNTS = [
    76561199012209167,
    76561198983283612,
    76561198430222108,
    76561198987392766,
    76561198322324484,
    76561198928360529,
    76561199098269026,
    76561198383259619,
    76561198956330397,
    76561198399774744,
    76561198820131954,
    76561198810477896,
    76561198214904576,
    76561199009358779,
    76561198997601760,
    76561198099746925,
    76561198992278402
    ]
i = 1
INTERVAL = 5 * 60
RANDOM_INTERVAL = 2 * 60
BEFORE = datetime.now()
NEW_INTERVAL = 0
while 1:
    NOW = datetime.now()
    if (NOW - BEFORE).seconds > NEW_INTERVAL:
        BEFORE = NOW
        i += 1
        NEW_INTERVAL = INTERVAL + randint(-RANDOM_INTERVAL, RANDOM_INTERVAL)
        if i==len(ACCOUNTS): i=0
        inventory = get_inventory(ACCOUNTS[i], True)
        if inventory is not None:
            print(f'{i}: {inventory}')
        print(f'{i} checked. Next check in {NEW_INTERVAL} seconds')
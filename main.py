import pyautogui as pg
import tkinter as tk
from random import choices
import json
import string
import os
import time
import gspread
from termcolor import colored, cprint
import requests
from colorama import just_fix_windows_console
from datetime import datetime
from sys import exit

def help():
    cprint("<LIST OF ALL COMMANDS>", 'green', attrs=['bold'])
    cprint("  ● Show this message: help", 'white')
    cprint("  ● Start instances: start --test/-t/-T for testing mode", 'white')
    cprint("  ● Update spreadsheet: update", 'white')
    cprint("  ● List accounts: list", 'white')
    cprint("  ● Price drops: price --specific/-s/-S to update specific drops", 'white')
    cprint("  ● Get inventory: inventory --drops/-d/-D to show drops only", 'white')
    cprint("  ● Exit: exit", 'white')

def price_drops(specific_drop):
    chosen_drops = []
    drops = list(Drops.keys())
    if not specific_drop: chosen_drops = drops
    else:
        l = list(map(lambda item: item.strip(),input("Enter drops: ").lower().split(',')))
        for i in l:
            for j in drops:
                if i in j.lower():
                    chosen_drops.append(j)
                    break
            else:
                cprint(f"{i} not found", 'red', attrs=['bold'])
    cprint("Updating drops prices...", 'yellow', attrs=['bold'])
    gc = gspread.service_account()
    sh = gc.open("Ферма")
    sheet = sh.worksheet("Дропы")
    for drop in chosen_drops:
        time.sleep(0.1)
        price = None
        try:
            r = requests.get("https://steamcommunity.com/market/priceoverview/?country=RU&currency=5&appid=730&market_hash_name=" + Drops[drop])
            price = r.json()["lowest_price"]
            price = price.replace(" pуб.", "") # deleting " pуб." from price
            sheet.update_acell(f"C{drops.index(drop)+2}", price) 
            sheet.update_acell(f"D{drops.index(drop)+2}", datetime.now().strftime("%d.%m.%Y %H:%M:%S"))
            cprint(f"  ● {drop}: {price} руб. Updated", 'green', attrs=['bold'])
        except TypeError:
            cprint(f"  ● {drop}: Not updated", 'red', attrs=['bold'])

def get_inventory(steamid, drops_only):
    cprint(f"Accessing inventory of {steamid}", 'yellow', attrs=['bold'])
    data = requests.get(f'https://steamcommunity.com/inventory/{steamid}/730/2?l=english&count=5000')
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

def list_accounts():
    cprint("<LIST OF ALL ACCOUNTS>", 'green', attrs=['bold'])
    for i in accounts:
        cprint(f"  ● Account {i['Номер']}: {i['SteamID']} {i['Логин']}:{i['Пароль']} {i['Телефон']} {i['Почта']}",'white')

def update_spreadsheet():
    global sh, accounts
    cprint("Updating spreadsheet...", 'yellow', attrs=['bold'])
    try:
        gc = gspread.service_account()
        cprint("Service account file loaded.", 'green', attrs=['bold'])
    except FileNotFoundError:
        if os.path.exists('service_account.json'):
            cprint("Service account file found.", 'green', attrs=['bold'])
            appdata = os.getenv('APPDATA')
            path = appdata + '\\gspread'
            cprint("Moving service account file to {}".format(path), 'yellow', attrs=['bold'])
            os.makedirs(path, exist_ok=True)
            os.rename("service_account.json",f"{path}\\service_account.json")
            gc = gspread.service_account()
            cprint("Service account file loaded.", 'green', attrs=['bold'])
        else:
            cprint("Service account file not found.", 'red', attrs=['bold'])
            cprint("Please download service account file and put it in the same folder", 'red', attrs=['bold'])
            input()
            exit()
    sh = gc.open("Ферма")
    accounts = sh.sheet1.get_all_records()
    cprint("Loaded {} accounts".format(len(accounts)), 'green', attrs=['bold'])

def start_instances(sheet1, isTesting):
    accounts = {str(n+1):{"login":str(i['Логин']), "password":str(i['Пароль'])} for n,i in enumerate(sheet1)}
    width, height = pg.size()
    maxValue = (width//400) * (height//300)
    while 1:
        print("Select accounts: ")
        selection = input().split()
        if len(selection)==0:
            cprint("No accounts selected", 'red', attrs=['bold'])
            continue
        selectedAccounts = set()
        for num, i in enumerate(selection):
            if i.isdigit() and int(i)>0:
                selectedAccounts.add(int(i))
            elif '-' in i:
                start = i.split('-')[0]
                end = i.split('-')[1]
                if start.isdigit() and end.isdigit():
                    selectedAccounts |= set(range(max(1,int(start)), int(end)+1))
            else:
                cprint("Invalid input in {} argument".format(num+1), 'red', attrs=['bold'])
                continue
        n = len(selectedAccounts)
        if n>maxValue or n>len(accounts):
            cprint("Too many accounts selected. You can select up to {} accounts".format(min(maxValue, len(accounts))), 'red', attrs=['bold'])
            continue
        ans = input(colored("Are you sure you want to select {} accounts? (y/n): ".format(n), 'yellow', attrs=['bold']))
        if ans=='y': break
    selectedAccounts = list(selectedAccounts)
    cprint("Calculating distribution...", 'yellow', attrs=['bold'])
    root = tk.Tk()
    root.geometry(f"{width//10}x{height//10}")
    root.title("Distribution")
    root.resizable(False, False)
    colors = [f"#{''.join(choices(string.hexdigits, k=6))}" for i in range(n)]
    screens = [tk.Frame(root,width=40, height=30, bg=colors[i]) for i in range(n)]
    labels = [tk.Label(screens[i], text = f"{selectedAccounts[i]}", font="Arial 10 bold", bg = colors[i]) for i in range(n)]
    distributions = [(i, j) for j in range(1, n+1) for i in range(1, n+1) if i*j >= n and i*400 < width and j*300 < height]
    distributions.sort(key = lambda x: abs(x[0]-x[1]))
    distributions.sort(key = lambda x: abs(x[0]*x[1] - n))
    distribution = distributions[0]
    padX = (width - distribution[0]*400) // (distribution[0]+1)
    padY = (height - distribution[1]*300) // (distribution[1]+1)
    windowsCoordinates = [(padX*(x+1)+x*400,padY*(y+1)+y*300) for y in range(distribution[1]) for x in range(distribution[0])]
    cprint("Distribution calculated. Screenspace coordinates:", 'white', attrs=['bold'])
    for i in range(n): print("Account {}: {}".format(selectedAccounts[i], windowsCoordinates[i]))
    for i in range(n):
        screens[i].place(x=windowsCoordinates[i][0]//10, y=windowsCoordinates[i][1]//10)
        screens[i].pack_propagate(False)
        labels[i].place(relx=0.5, rely=0.5, anchor=tk.CENTER)
    for i in range(n):
        accountActivationString = cmdstring.replace('X', str(windowsCoordinates[i][0])).replace('Y', str(windowsCoordinates[i][1]))
        if '-login' in cmdstring:
            account = accounts[str(selectedAccounts[i])] # accounts is a dictionary
            accountActivationString = accountActivationString.replace('LOGIN', account['login']).replace('PASSWORD', account['password'])
            cprint(f"Account initialized: {account['login']}", 'green', attrs=['bold'])
        cprint(f"Command: {accountActivationString}", 'white', attrs=['dark'])
        if isTesting: cprint("Testing mode. Skipping lauching...", 'yellow', attrs=['bold'])
        else:
            os.system(accountActivationString)
            time.sleep(1)
    root.mainloop()

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

cprint("Welcome to Farm Manager", 'magenta', attrs=['bold'])
cprint('  by pirantel', 'magenta', attrs=['bold'])
cprint("Type 'help' to see all commands", 'magenta', attrs=['bold'])

try:
    data = open('config.json', 'r')
    cprint("Config file loaded.", 'green', attrs=['bold'])
except FileNotFoundError:
    cprint("Config file not found.", 'yellow', attrs=['bold'])
    cprint("Creating config file...", 'yellow', attrs=['bold'])
    PossiblePaths = [r"X:\Steam\steam.exe", r"X:\Program Files\Steam\steam.exe", r"X:\Program Files (x86)\Steam\steam.exe"]
    ValidHardPaths = []
    for Drive in string.ascii_uppercase:
        for path in PossiblePaths:
            path = path.replace("X", Drive)
            if os.path.exists(path):
                ValidHardPaths.append(path)
    if len(ValidHardPaths) == 0:
        cprint("Steam not found. Please enter path to steam.exe", 'red', attrs=['bold'])
        steamPath = input()
    elif len(ValidHardPaths) == 1:
        steamPath = ValidHardPaths[0]
        cprint(f"Steam found at {steamPath}", 'green', attrs=['bold'])
    else:
        cprint("Steam found at multiple locations:", 'yellow', attrs=['bold'])
        for i in range(len(ValidHardPaths)):
            cprint(f"{i+1}. {ValidHardPaths[i]}", 'white', attrs=['bold'])
        cprint("Please enter number of correct path", 'yellow', attrs=['bold'])
        steamPath = ValidHardPaths[int(input(':'))-1]
    data = open('config.json', 'w')
    data.write(json.dumps({"steampath": steamPath, "cmdcommand": "start \"\" STEAMPATH -login LOGIN PASSWORD -language russian -applaunch 730 -low -nohltv -nosound -novid -window -w 640 -h 480 +connect 192.168.1.106:27027 +exec farm.cfg -x X -y Y"}))
    data.close()
    data = open('config.json', 'r')
    cprint("Config file loaded.", 'green', attrs=['bold'])
jsondata = json.load(data)
cmdstring = jsondata["cmdcommand"].replace('STEAMPATH', jsondata["steampath"])
sh = []
accounts = []
update_spreadsheet()
if len(accounts)==0:
    cprint("No accounts found.", 'red', attrs=['bold'])

while 1: # main loop
    try:
        mode, *args = input(":").lower().split()
    except ValueError:
        continue
    if mode in ['help']:
        help()
    elif mode in ['start']:
        start_instances(accounts, '--test' in args or '-t' in args)
    elif mode in ['update']:
        update_spreadsheet()
    elif mode in ['list']:
        list_accounts()
    elif mode in ['price']:
        price_drops('--specific' in args or '-s' in args)
    elif mode in ['inventory']:
        number = input(colored(f"Enter SteamID or account number between 1 and {len(accounts)}: ", 'yellow', attrs=['bold']))
        if number.isdigit():
            number = int(number)
            if number>0 and number<=len(accounts): number = str(accounts[number-1]['SteamID'])
        inventory = get_inventory(number, '--specific' in args or '-s' in args)
        if inventory == None:
            cprint("Error getting inventory", 'red', attrs=['bold'])
            continue
        if len(inventory) == 0:
            cprint("Inventory is empty", 'yellow', attrs=['bold'])
            continue
        else:
            for item, count in inventory.items():
                cprint(f"  ● {item} x {count}", 'white', attrs=['bold'])
    elif mode in ['exit']:
        cprint("Exiting...", 'yellow', attrs=['bold'])
        exit()
    else:
        cprint("Unknown command", 'red', attrs=['bold'])
import pyautogui as pg
from random import choices
import json
import string
import os
import time
import gspread
from termcolor import colored, cprint
import requests
from colorama import just_fix_windows_console
from datetime import datetime, timedelta
from sys import exit
from subprocess import Popen
import socket
from rcon.source import Client
import keyboard
from steampy.models import GameOptions, Asset
from steampy.client import SteamClient

def help() -> None:
    cprint("<LIST OF ALL COMMANDS>", 'green', attrs=['bold'])
    cprint("  ● Show this message: help", 'white')
    cprint("  ● Start server: server", 'white')
    cprint("  ● Start instances: start --test/-t/-T for testing mode --restart/-r/-R to restart account", 'white')
    cprint("  ● Update server: update", 'white')
    cprint("  ● List accounts: list", 'white')
    cprint("  ● Price drops: price --specific/-s/-S to update specific drops", 'white')
    cprint("  ● Get inventory: inventory --drops/-d/-D to show drops only", 'white')
    cprint("  ● Enable RCON connection: rcon --command/-c/-C to send commands", 'white')
    cprint("  ● Monitor drops: monitor", 'white')
    cprint("  ● Send trade offer: trade --drop/-d/-D to send to central", 'white')
    cprint("  ● Exit: exit", 'white')

def price_drops(specific_drop: bool) -> None:
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
            r = requests.get("https://steamcommunity.com/market/priceoverview/?country=RU&currency=5&appid=730&market_hash_name=" + Drops[drop][0])
            price = r.json()["lowest_price"]
            price = price.replace(" pуб.", "") # deleting " pуб." from price
            sheet.update_acell(f"C{drops.index(drop)+2}", price) 
            sheet.update_acell(f"D{drops.index(drop)+2}", datetime.now().strftime("%d.%m.%Y %H:%M:%S"))
            cprint(f"  ● {drop}: {price} руб. Updated", 'green', attrs=['bold'])
        except TypeError:
            cprint(f"  ● {drop}: Not updated", 'red', attrs=['bold'])

def get_inventory(steamid: str, drops_only: bool, toTrade: bool = False) -> dict/list:
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
    if toTrade:
        assets = [(Asset(asset['assetid'], GameOptions('730','2'), asset['amount']), asset['classid']) for asset in json_data['assets']]
        descriptions = {description['classid']:description['tradable'] for description in json_data['descriptions']}
        tradable_assets = [asset[0] for asset in assets if descriptions[asset[1]] == 1]
        return tradable_assets
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

def list_accounts() -> None:
    cprint("<LIST OF ALL ACCOUNTS>", 'green', attrs=['bold'])
    for i in accounts:
        cprint(f"  ● Account {i['Номер']}: {i['SteamID']} {i['Логин']}:{i['Пароль']} {i['Телефон']} {i['Почта']}",'white')

def update_spreadsheet() -> None:
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

def start_instances(sheet1: property, isTesting: bool) -> None:
    global coordinates_dict
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
    selectedAccounts = sorted(list(selectedAccounts))
    cprint("Calculating distribution...", 'yellow', attrs=['bold'])
    #root = tk.Tk()
    #root.geometry(f"{width//10}x{height//10}")
    #root.title("Distribution")
    #root.resizable(False, False)
    #colors = [f"#{''.join(choices(string.hexdigits, k=6))}" for i in range(n)]
    #screens = [tk.Frame(root,width=40, height=30, bg=colors[i]) for i in range(n)]
    #labels = [tk.Label(screens[i], text = f"{selectedAccounts[i]}", font="Arial 10 bold", bg = colors[i]) for i in range(n)]
    distributions = [(i, j) for j in range(1, n+1) for i in range(1, n+1) if i*j >= n and i*400 < width and j*300 < height]
    distributions.sort(key = lambda x: abs(x[0]-x[1]))
    distributions.sort(key = lambda x: abs(x[0]*x[1] - n))
    distribution = distributions[0]
    padX = (width - distribution[0]*400) // (distribution[0]+1)
    padY = (height - distribution[1]*300) // (distribution[1]+1)
    windowsCoordinates = [(padX*(x+1)+x*400,padY*(y+1)+y*300) for y in range(distribution[1]) for x in range(distribution[0])]
    coordinates_dict = {str(selectedAccounts[i]):windowsCoordinates[i] for i in range(n)}
    cprint("Distribution calculated. Screenspace coordinates:", 'white', attrs=['bold'])
    for i in range(n): print("Account {}: {}".format(selectedAccounts[i], windowsCoordinates[i]))
    #for i in range(n):
    #    screens[i].place(x=windowsCoordinates[i][0]//10, y=windowsCoordinates[i][1]//10)
    #    screens[i].pack_propagate(False)
    #    labels[i].place(relx=0.5, rely=0.5, anchor=tk.CENTER)
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

def get_steampath() -> str:
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
    return steamPath

def get_steamcmdpath() -> str:
    cprint("SteamCMD path not set.", 'yellow', attrs=['bold'])
    drives = [ chr(x) + ":" for x in range(65,91) if os.path.exists(chr(x) + ":") ]
    steamcmdpath = ''
    for drive in drives:
        for r,d,f in os.walk(drive + '\\'):
            if 'steamcmd' not in r.lower(): continue
            if 'steamcmd.exe' in f:
                steamcmdpath = r
                break
    cprint(f"SteamCMD found at: {steamcmdpath}\\steamcmd.exe", 'green', attrs=['bold'])
    return steamcmdpath

def update_server() -> None:
    cprint("Updating server...", 'yellow', attrs=['bold'])
    Popen('steamcmd.exe +login anonymous +app_update 740 validate +quit', cwd=steamcmdpath, shell=True)

def start_server() -> None:
    cprint("Starting server...", 'yellow', attrs=['bold'])
    Popen("srcds -game csgo -console -usercon -nobots -port 27027 -usercon -console +game_type 0 +game_mode 0 +mapgroup mg_custom +map achievement_idle +sv_logflush 1 +log on +sv_log_onefile 1",
    cwd=steamcmdpath + r"\steamapps\common\Counter-Strike Global Offensive Beta - Dedicated Server", shell=True)

def check_drops(logs: list) -> None:
    #example: L 07/26/2020 - 22:53:56: [DropsSummoner.smx] Игроку XyLiGaN<226><STEAM_1:0:558287561><> выпало [4281-0-1-4]
    for log in logs:
        if '[DropsSummoner.smx]' not in log: continue
        log = log.split(' ')
        player = log[6]
        player = player[:player.find('<')]
        drop = log[8]
        drop = drop.split('-')[0][1:]
        for skin, r in Drops.items():
            if r[1] == drop:
                drop = skin
        now = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        cprint(f"Account {player} received {drop}  {now}", 'white', attrs=['bold'])
        send_trade(player, '76561198064460092')
        sheet2 = sh.get_worksheet(2)
        i = len(sheet2.get_all_records()) + 2
        sheet2.update_acell(f"A{i}", player)
        sheet2.update_acell(f"B{i}", drop)
        sheet2.update_acell(f"C{i}", now)

def monitor_drops() -> None:
    global last_log
    path = steamcmdpath + "\\steamapps\\common\\Counter-Strike Global Offensive Beta - Dedicated Server\\csgo\\logs\\"
    dir = os.listdir(path)
    if len(dir) == 0:
        cprint("No logs found. Please start server first.", 'red', attrs=['bold'])
        return
    interval = 10
    before = datetime.now()
    before -= timedelta(seconds=interval)
    cprint("Monitoring drops...", 'yellow', attrs=['bold'])
    cprint("Press 'q' to stop monitoring.", 'yellow', attrs=['bold'])
    while not keyboard.is_pressed('q'):
        now = datetime.now()
        if (now - before).seconds < interval: continue
        before = datetime.now()
        logs = open(path + dir[0], 'r', encoding= 'utf-8').read().split('\n')[:-1]
        new_logs = logs[len(last_log):]
        last_log = logs
        n = len(new_logs)
        if n>0:
            cprint(f"Found {n} new logs:", 'blue', attrs=['bold'])
            check_drops(new_logs)
        else:
            cprint("No new logs", 'red', attrs=['bold'])      
    
def restart_account(sheet1: property, account_number: int, isTesting: bool) -> None:
    accounts = {str(n+1):{"login":str(i['Логин']), "password":str(i['Пароль'])} for n,i in enumerate(sheet1)}
    cprint(f"Restarting account {account_number}...", 'yellow', attrs=['bold'])   
    account = accounts[str(account_number)] # accounts is a dictionary
    accountActivationString = cmdstring.replace('LOGIN', account['login']).replace('PASSWORD', account['password']).replace('X', str(coordinates_dict[str(account_number)][0])).replace('Y', str(coordinates_dict[str(account_number)][1]))
    cprint(f"Account initialized: {account['login']}", 'green', attrs=['bold'])
    cprint(f"Command: {accountActivationString}", 'white', attrs=['dark'])
    if not isTesting:
        os.system(accountActivationString)
    else: cprint("Testing mode. Skipping lauching...", 'yellow', attrs=['bold'])

def get_local_ip() -> str:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('192.255.255.255', 1))
        IP = s.getsockname()[0]
    except:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

def get_rconpassword() -> str:
    path = steamcmdpath + '\\steamapps\\common\\Counter-Strike Global Offensive Beta - Dedicated Server\\csgo\\cfg\\server.cfg'
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        for line in lines:
            if line.startswith('rcon_password'):
                password = line.split(' ')[1].replace('"', '')
                cprint('RCON password: ' + password, 'green', attrs=['bold'])
                break
        else:
            cprint('RCON password not found', 'red', attrs=['bold'])
            return
    return password

def rcon_command(client: Client, command: str) -> None:
    response = client.run(command)
    cprint(response, 'white')

def rcon_connection() -> Client:
    try:
        client = Client(local_ip, 27027, passwd=get_rconpassword())
        client.connect(login=True)
        cprint('Connected to RCON', 'green', attrs=['bold'])
        return client
    except ConnectionRefusedError:
        cprint('Connection refused', 'red', attrs=['bold'])
        return

def send_trade(account_number: int, othersteamid: str) -> None:
    api_key = accounts[account_number - 1]['API']
    login = accounts[account_number - 1]['Логин']
    password = accounts[account_number - 1]['Пароль']
    steamid = accounts[account_number - 1]['SteamID']
    secret = accounts[account_number - 1]['SECRET']
    tradable_assets = get_inventory(steamid, False, True)
    if tradable_assets is None:
        cprint(f"Account {account_number} has no tradable items", 'red', attrs=['bold'])
        return
    cprint(f'Found {len(tradable_assets)} tradable items', 'green', attrs=['bold'])
    try:
        with SteamClient(api_key, login, password, secret) as client:
            client.make_offer(tradable_assets, [], othersteamid, 'hi')
            cprint(f"Trade offer sent to {othersteamid}", 'green', attrs=['bold'])
    except Exception as e:
        cprint(f"Error: {e}", 'red', attrs=['bold'])
        return

Drops = {'Fracture Case': ('Fracture%20Case',"4698"),
         'Dreams and Nightmares Case': ('Dreams%20%26%20Nightmares%20Case',"4818"),
         'Recoil Case': ('Recoil%20Case',"4846"),
         'Clutch Case': ('Clutch%20Case',"4471"),
         'Snakebite Case': ('Snakebite%20Case',"4747"),
         'Operation Phoenix Weapon Case': ('Operation%20Phoenix%20Weapon%20Case',"4011"),
         'Huntsman Weapon Case': ('Huntsman%20Weapon%20Case',"4017"),
         'CS:GO Weapon Case': ('CS%3AGO%20Weapon%20Case',"4001"),
         'Operation Bravo Case': ('Operation%20Bravo%20Case',"4003"),
         'Spectrum Case': ('Spectrum%20Case',"4351"),
         'Sticker Capsule': ('Sticker%20Capsule',"4007"),
         'Danger Zone Case': ('Danger%20Zone%20Case',"4548"),
         'Chroma 2 Case': ('Chroma%202%20Case',"4089"),
         'Operation Wildfire Case': ('Operation%20Wildfire%20Case',"4187"),
         'Spectrum 2 Case': ('Spectrum%202%20Case',"4403"),
         'Chroma Case': ('Chroma%20Case',"4061"),
         'Community Sticker Capsule 1': ('Community%20Sticker%20Capsule%201',"4016"),
         'Winter Offensive Weapon Case': ('Winter%20Offensive%20Weapon%20Case',"4009"),
         'Sticker Capsule 2': ('Sticker%20Capsule%202',"4012"),
         'Prisma Case': ('Prisma%20Case',"4598"),
         'Horizon Case': ('Horizon%20Case',"4482"),
         'Falchion Case': ('Falchion%20Case',"4091"),
         'Operation Vanguard Weapon Case': ('Operation%20Vanguard%20Weapon%20Case',"4029"),
         'Gamma Case': ('Gamma%20Case',"4236"),
         'Prisma 2 Case': ('Prisma%202%20Case',"4695"),
         'Shadow Case': ('Shadow%20Case',"4138"),
         'Glove Case': ('Glove%20Case',"4288"),
         'Revolver Case': ('Revolver%20Case',"4186"),
         'Operation Hydra Case': ('Operation%20Hydra%20Case',"4352"),
         'CS20 Case': ('CS20%20Case',"4669"),
         'Operation Breakout Weapon Case': ('Operation%20Breakout%20Weapon%20Case',"4018"),
         'CS:GO Weapon Case 2': ('CS%3AGO%20Weapon%20Case%202',"4004"),
         'CS:GO Weapon Case 3': ('CS%3AGO%20Weapon%20Case%203',"4010"),
         'Gamma 2 Case': ('Gamma%202%20Case',"4281"),
         'Chroma 3 Case': ('Chroma%203%20Case',"4233")
         }

just_fix_windows_console()

cprint("Welcome to Farm Manager", 'magenta', attrs=['bold'])
cprint('  by pirantel', 'magenta', attrs=['bold'])
cprint("Type 'help' to see all commands", 'magenta', attrs=['bold'])

try:
    data = open('config.json', 'r')
    cprint("Config file loaded.", 'green', attrs=['bold'])
except FileNotFoundError:
    cprint("Creating config file...", 'yellow', attrs=['bold'])
    data = open('config.json', 'w')
    data.write(json.dumps({"steamcmdpath": get_steamcmdpath(), "steampath": get_steampath(), "cmdcommand": "start \"\" STEAMPATH -login LOGIN PASSWORD -language russian -applaunch 730 -low -nohltv -nosound -novid -window -w 640 -h 480 +connect IP +exec farm.cfg -x X -y Y"}))
    data.close()
    data = open('config.json', 'r')
    cprint("Config file loaded.", 'green', attrs=['bold'])

jsondata = json.load(data)
steamcmdpath = jsondata["steamcmdpath"]
local_ip = get_local_ip()
cmdstring = jsondata["cmdcommand"].replace('STEAMPATH', jsondata["steampath"]).replace('IP',  local_ip + ":27027")

sh = []
accounts = []
update_spreadsheet()
if len(accounts)==0:
    cprint("No accounts found.", 'red', attrs=['bold'])
coordinates_dict = {}
last_log = []
while 1: # main loop
    try:
        mode, *args = input(":").lower().split()
    except ValueError:
        continue
    if mode in ['help']:
        help()
    elif mode in ['trade']:
        this = int(input(colored("Enter sender account number: ", 'yellow', attrs=['bold'])))
        other = '76561198064460092' if '--drop' in args or '-d' in args else input(colored("Enter receiver steamid: ", 'yellow', attrs=['bold']))
        cprint(f"Sending trade from {this} to {other}", 'yellow', attrs=['bold'])
        send_trade(this, other)
    elif mode in ['monitor']:
        monitor_drops()
    elif mode in ['rcon']:
        client = rcon_connection()
        if client and ('--command' in args or '-c' in args):
            cprint("Enter 'quit' to exit RCON", 'yellow', attrs=['bold'])
            while 1:
                command = input(colored(':>', 'white', attrs=['bold']))
                if command == 'quit': break
                rcon_command(client, command)
                if command == 'exit': break
    elif mode in ['start']:
        isTesting = '--test' in args or '-t' in args
        if '--restart' in args or '-r' in args:
            n = input(colored(f"Enter account number to restart: ", 'yellow', attrs=['bold']))
            if n not in coordinates_dict.keys():
                cprint(f"Account number {n} was not started.", 'red', attrs=['bold'])
                cprint(f"List of started accounts: {' '.join(coordinates_dict.keys())}", 'red', attrs=['bold'])
                continue
            
            restart_account(accounts, n, isTesting)
            continue
        start_instances(accounts, isTesting)
    elif mode in ['server']:
        path = steamcmdpath + "\\steamapps\\common\\Counter-Strike Global Offensive Beta - Dedicated Server\\csgo\\logs\\"
        for file in os.listdir(path):
            try:
                os.remove(path + file)
            except PermissionError:
                pass
        last_log = []
        start_server()
    elif mode in ['update']:
        update_server()
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
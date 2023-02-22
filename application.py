import customtkinter as ctk
import tkinter as tk
import gspread
import requests
import json
from steampy.models import GameOptions, Asset
from steampy.client import SteamClient
from steampy.guard import generate_one_time_code
import os
from subprocess import Popen
from rcon.source import Client
import socket
from datetime import datetime
import pyautogui as pg
import autoit
from time import sleep
import signal

ctk.set_default_color_theme('green')

class Panel(ctk.CTkFrame):
    def __init__(self, parent: ctk.CTk, *args, **kwargs) -> None:
        super().__init__(parent, *args, **kwargs)
        self.consoleText = ctk.CTkTextbox(self,width = parent.width//2,height=parent.height * 2 // 3, fg_color = ('#1D1E1E','#1D1E1E'), state = 'disabled', font=('Consolas', 14))
        self.consoleText.pack(anchor='center')
    def AddText(self, message: str, color: str = 'white') -> None:
        self.consoleText.tag_config(color, foreground = color)
        self.consoleText.configure(state = 'normal')
        self.consoleText.insert('end' , message, color)
        self.consoleText.configure(state = 'disabled')
    def UpdateStatus(self, index: int, message: str, color: str):
        self.consoleText.tag_config(color, foreground = color)
        self.consoleText.configure(state = 'normal')
        text = self.consoleText.get(str(float(index)),f"{index+1}.0")
        startIndex = f"{index}.{text.index(text.split()[-1])}"
        self.consoleText.delete(startIndex,str(float(index)+1))
        self.consoleText.insert(startIndex, message + '\n', color)
        self.consoleText.configure(state = 'disabled')

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.version = '2.0'
        self.width = 800
        self.height = 600
        self.title(f"Farm Manager v{self.version}")
        self.geometry(f"{self.width}x{self.height}")
        self.resizable(False, False)
        self.grid_columnconfigure((0,1), weight=0)
        self.grid_rowconfigure((0,1), weight=0)

        self.panel = Panel(self, width=self.width // 2, height = self.height * 2 // 3)
        self.panel.grid(row = 1, column = 1, sticky = 'nsew')
        self.panel.grid_propagate(False)
    
        self.console = Console(self, width=self.width//2, height=self.height // 3)
        self.console.grid(row = 0, column = 1, sticky = 'nsew')
        self.console.grid_propagate(False)

        self.options = Options(self, width = self.width // 2, height = self.height // 3)
        self.options.grid(row = 0, column = 0, sticky = 'nsew')
        self.options.grid_propagate(False)
        self.options.ChangeScale('100%')
        self.options.ChangeAppearanceMode('Dark')

        self.utils = Utils(self)
        self.accounts = self.utils.getAccounts()
        for account in self.accounts:
            text = f"[{account.number}]{' ' * (4-len(str(account.number)))}{account.login}"
            self.panel.AddText(text)
            status = account.status
            spaces = (30 - len(text)) * ' '
            if status=='OFF':  self.panel.AddText(f"{spaces}{account.status}\n", "red")
            elif status=='LAUNCHING': self.panel.AddText(f"{spaces}{account.status}\n", "yellow")
            elif status=='LAUNCHED': self.panel.AddText(f"{spaces}{account.status}\n", "green")
            elif status=='DROPPED': self.panel.AddText(f"{spaces}{account.status}\n", "blue")

        self.methods = Methods(self, width = self.width // 2, height = self.height * 2 // 3)
        self.methods.grid(row = 1, column = 0, sticky = 'nsew')
        self.methods.grid_propagate(False)

        self.update()

class Console(ctk.CTkFrame):
    def __init__(self, parent: ctk.CTk, *args, **kwargs) -> None:
        super().__init__(parent, *args, **kwargs)
        self.consoleText = ctk.CTkTextbox(self,width = parent.width//2,height=parent.height // 3, fg_color = ('#1D1E1E','#1D1E1E'), state = 'disabled', font=('Consolas', 10))
        self.consoleText.pack()
        self.Log('Console initialized')

    def Log(self, message: str, color: str = 'white') -> None:
        self.consoleText.tag_config(color, foreground = color)
        self.consoleText.configure(state = 'normal')
        self.consoleText.insert('end' ,f"[{datetime.now().strftime('%H:%M:%S')}] {message}\n", color)
        self.consoleText.see('end')
        self.consoleText.configure(state = 'disabled')

class StatusLabel(ctk.CTkButton):
    def __init__(self, parent, object: str, status: str, *args, **kwargs) -> None:
        super().__init__(parent, *args, **kwargs)
        self.object = object
        self.status = status
        self.configure(text = f'{self.object}: {self.status}')
    
    def SetStatus(self, status: str) -> None:
        self.status = status
        self.configure(text = f'{self.object}: {self.status}')

class Options(ctk.CTkFrame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.parent = parent
        
        self.settingslabel = ctk.CTkLabel(self, text = 'SETTINGS', font = ('Robotto', 20, 'bold'))
        self.settingslabel.grid(row = 0, column = 0, sticky = 'nw', padx = 20, pady = 8)

        self.appearanceModeMenu = ctk.CTkOptionMenu(self, variable=tk.StringVar(value="Theme"), values=['Dark', 'Light', 'System'], command=self.ChangeAppearanceMode)
        self.appearanceModeMenu.grid(row = 1, column = 0, sticky = 'nsew', padx = 20, pady = 8)

        self.scaleMenu = ctk.CTkOptionMenu(self, variable=tk.StringVar(value="Scale"), values=["50%", "60%", "70%", "80%", "90%", "100%", "110%", "120%", "130%", "140%", "150%"], command=self.ChangeScale)
        self.scaleMenu.grid(row = 2, column = 0, sticky = 'nsew', padx = 20, pady = 8)

        self.configstatus = StatusLabel(self, 'Config', 'NO', corner_radius = 10, border_width = 0, fg_color = ["gray86", "gray17"], text_color = ['black','white'] , hover_color = 'grey')
        self.configstatus.grid(row = 0, column = 1, sticky = 'nsew', padx = 20, pady = 8)

        self.servicestatus = StatusLabel(self, 'Service account', 'NO', corner_radius = 10, border_width = 0, fg_color = ["gray86", "gray17"], text_color = ['black','white'] , hover_color = 'grey', command = lambda: self.GetPathDialog('serviceAccountPath'))
        self.servicestatus.grid(row = 1, column = 1, sticky = 'nsew', padx = 20, pady = 8)

        self.steamstatus = StatusLabel(self, 'Steam', 'NO', corner_radius = 10, border_width = 0, fg_color = ["gray86", "gray17"], text_color = ['black','white'] , hover_color = 'grey', command = lambda: self.GetPathDialog('steampath'))
        self.steamstatus.grid(row = 2, column = 1, sticky = 'nsew', padx = 20, pady = 8)

        self.steamcmdstatus = StatusLabel(self, 'SteamCMD', 'NO', corner_radius = 10, border_width = 0, fg_color = ["gray86", "gray17"], text_color = ['black','white'] , hover_color = 'grey', command = lambda: self.GetPathDialog('steamcmdpath'))
        self.steamcmdstatus.grid(row = 3, column = 1, sticky = 'nsew', padx = 20, pady = 8)

        self.updateFilesbtn = ctk.CTkButton(self, text = 'Update files', command = self.UpdateFiles)
        self.updateFilesbtn.grid(row = 3, column = 0, sticky = 'nsew', padx = 20, pady = 8)

    def GetPathDialog(self, file: str):
        dialog = ctk.CTkInputDialog(title = f'PATH', text = f'Enter {file}')
        self.UpdateConfig({file: dialog.get_input()})

    def UpdateConfig(self, data: dict):
        file = open('config.json', 'r').read()
        file = json.loads(file)
        for key, value in data.items():
            file[key] = value
        file = json.dumps(file)
        open('config.json', 'w').write(file)

    def UpdateFiles(self):
        self.parent.console.Log('Updating files...', 'yellow')
        self.parent.utils.connectServiceAccount()
        self.parent.utils.connectConfig()

    def ChangeScale(self, scale: str) -> None:
        new_scaling_float = int(scale.replace("%", "")) / 100
        ctk.set_widget_scaling(new_scaling_float)
        ctk.set_window_scaling(new_scaling_float)
        self.parent.console.Log(f'Scale changed to {scale}', 'green')

    def ChangeAppearanceMode(self, mode: str) -> None:
        ctk.set_appearance_mode(mode)
        self.parent.console.Log(f'Appearance mode changed to {mode}', 'green')

class Methods(ctk.CTkFrame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.parent = parent

        self.localip = self.GetLocalIP()
        self.steampath = self.parent.utils.config['steampath']
        self.steamcmdpath = self.parent.utils.config['steamcmdpath']
        self.cmdcommand = self.parent.utils.config['cmdcommand'].replace('STEAMPATH', self.steampath).replace('IP', self.localip + ':27027')

        self.last_logs = []
        self.tradestack = []
        self.coordinates_dict = {}
        self.accountQueue = []
        self.TradeStackStart()
        self.CheckActiveAccounts()

        self.serverlabel = ctk.CTkLabel(self, text = 'SERVER TOOLS', font = ('Robotto', 20, 'bold'))
        self.serverlabel.grid(row = 0, column = 0, sticky = 'nw', padx = 15, pady = 8)

        self.serverstatus = StatusLabel(self, 'Server', 'NO', corner_radius = 10, border_width = 0, fg_color = ["gray86", "gray17"], text_color = ['black','white'] , hover_color = 'grey')
        self.serverstatus.grid(row = 0, column = 1, sticky = 'nsew', padx = 15, pady = 8)

        self.startserverbtn = ctk.CTkButton(self, text = 'Start server', command = self.StartServer, width=150)
        self.startserverbtn.grid(row = 1, column = 0, sticky = 'nsew', padx = 15, pady = 8)

        self.updateserverbtn = ctk.CTkButton(self, text = 'Update server', command = self.UpdateServer, width=150)
        self.updateserverbtn.grid(row = 1, column = 1, sticky = 'nsew', padx = 15, pady = 8)

        self.sendcommandbtn = ctk.CTkButton(self, text = 'RCON command', command = self.RCONCommand, width=150)
        self.sendcommandbtn.grid(row = 2, column = 0, sticky = 'nsew', padx = 15, pady = 8)

        self.rconconnectbtn = ctk.CTkButton(self, text = 'RCON connect', command = self.RCONConnection, width=150)
        self.rconconnectbtn.grid(row = 2, column = 1, sticky = 'nsew', padx = 15, pady = 8)

        self.farmlabel = ctk.CTkLabel(self, text = 'FARM TOOLS', font = ('Robotto', 20, 'bold'))
        self.farmlabel.grid(row = 3, column = 0, sticky = 'nw', padx = 15, pady = (30,8))

        self.maxAccounts = ctk.StringVar(self, 'Maximum')
        self.maxAccountsentr = ctk.CTkOptionMenu(self, variable = self.maxAccounts, values=[str(x) for x in range(1,len(self.parent.accounts))])
        self.maxAccountsentr.grid(row = 3, column = 1, sticky = 'nsew', padx = 15, pady = (30,8))

        self.listaccountbtn = ctk.CTkButton(self, text = 'List accounts', width=150, command=self.ListAccounts)
        self.listaccountbtn.grid(row = 4, column = 0, sticky = 'nsew', padx = 15, pady = 8)

        self.checkAccountsbtn = ctk.CTkButton(self, text = 'Check accounts', command = lambda: self.parent.utils.validateAccounts(self.parent.utils.getAccounts()), width=150)
        self.checkAccountsbtn.grid(row = 4, column = 1, sticky = 'nsew', padx = 15, pady = 8)

        self.pricedrops = ctk.CTkButton(self, text = 'Update drops', width=150, command = self.UpdatePrices)
        self.pricedrops.grid(row = 5, column = 0, sticky = 'nsew', padx = 15, pady = 8)

        self.monitoringbtn = ctk.CTkButton(self, text = 'Monitor drops', width=150, command=self.MonitorDrops)
        self.monitoringbtn.grid(row = 5, column = 1, sticky = 'nsew', padx = 15, pady = 8)

        self.startinstancesbtn = ctk.CTkButton(self, text = 'Start accounts', width=150, command=self.StartInstances)
        self.startinstancesbtn.grid(row = 6, column = 0, sticky = 'nsew', padx = 15, pady = 8)

        self.autoTrading = tk.BooleanVar(self, False)
        self.autotradingswitch = ctk.CTkSwitch(self, variable=self.autoTrading, text = 'Automatic trading', width=150, command= self.ChooseTradeId)
        self.autotradingswitch.grid(row = 6, column = 1, sticky = 'nsew', padx = 15, pady = 8)

        self.restartaccountbtn = ctk.CTkButton(self, text = 'Restart account', width=150, command=self.RestartAccount)
        self.restartaccountbtn.grid(row = 7, column = 0, sticky = 'nsew', padx = 15, pady = 8)

        self.isTesting = tk.BooleanVar(self, False)
        self.testswitch = ctk.CTkSwitch(self, variable = self.isTesting, text = 'Testing mode', width=150)
        self.testswitch.grid(row = 7, column = 1, sticky = 'nsew', padx = 15, pady = 8)

        self.test = ctk.CTkButton(self, text='test',command=lambda: list(self.coordinates_dict.values())[0].kill())
        self.test.grid(row=8,column=0)

        self.update()

    def TradeStackStart(self):
        if self.tradestack:
            self.tradestack.pop().sendTrade(self.autoTradingID)
            self.after(60000, self.TradeStackStart)
        else:
            self.after(10000, self.TradeStackStart)

    def ChooseTradeId(self):
        if self.autoTrading.get():
            tradedialog = ctk.CTkInputDialog(title='Enter SteamID', text='Enter SteamID to automatic trading')
            value = tradedialog.get_input()
            self.autoTradingID = value if value else "76561198064460092"
            self.log(f"Changed automatic trading ID to {self.autoTradingID}")
            print('changed to ', self.autoTradingID)

    def CheckActiveAccounts(self):
        print([x for x in self.accountQueue])
        print([(c,a) for c,a in self.coordinates_dict.items()])
        for coordinates, account in self.coordinates_dict.items():
            if account=='' and len(self.accountQueue)>0:
                newAccount = self.accountQueue.pop()
                self.coordinates_dict[coordinates] = newAccount
                self.log(f"Starting {newAccount.login}")
                newAccount.launch(self.cmdcommand.replace('LOGIN',str(newAccount.login)).replace('PASSWORD',str(newAccount.password)).replace('-x X','-x ' + str(coordinates[0])).replace('-y Y', '-y ' + str(coordinates[1])))
            if account and account.status == 'DROPPED':
                self.coordinates_dict[coordinates] = ""
        self.after(5000, self.CheckActiveAccounts)

    def StartInstances(self) -> None:
        testing = self.isTesting.get()
        accounts = self.parent.accounts

        n = int(self.maxAccounts.get())
        width, height = pg.size()
        distributions = [(i, j) for j in range(1, n+1) for i in range(1, n+1) if i*j >= n and i*400 < width and j*300 < height]
        distributions.sort(key = lambda x: abs(x[0]-x[1]))
        distributions.sort(key = lambda x: abs(x[0]*x[1] - n))
        distribution = distributions[0]
        padX = (width - distribution[0]*400) // (distribution[0]+1)
        padY = (height - distribution[1]*300) // (distribution[1]+1)
        windowsCoordinates = [(padX*(x+1)+x*400,padY*(y+1)+y*300) for y in range(distribution[1]) for x in range(distribution[0])]
        self.coordinates_dict = {(x[0],x[1]):"" for x in windowsCoordinates}
        
        selectaccounts = ctk.CTkInputDialog(title = 'Select accounts', text = 'Enter account numbers separated by spaces or ranges separated by dashes. Example: 1 2 3-5 6-10')
        selection = selectaccounts.get_input().split()
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
                self.log("Invalid input in {} argument".format(num+1), 'red')
                continue
        
        n = len(selectedAccounts)
        if n==0:
            self.log("No accounts selected", 'red')
            return
        if n>len(accounts):
            self.log("Too many accounts selected", 'red')
            return
        self.accountQueue = [accounts[x-1] for x in selectedAccounts]

    def RestartAccount(self):
        cmdstring = self.cmdcommand.replace('STEAMPATH', self.steampath).replace('IP', self.localip + ':27015')
        accountselection = ctk.CTkInputDialog(title = 'Select account', text = 'Enter one account to restart')
        account_number = accountselection.get_input()
        if account_number not in self.coordinates_dict:
            self.log("Account was not started", 'red')
            return
        testing = self.isTesting.get()
        account = self.parent.accounts[int(account_number)-1]
        self.log(f"Restarting account {account_number}...", 'yellow')   
        accountActivationString = cmdstring.replace('LOGIN', str(account.login)).replace('PASSWORD', str(account.password)).replace('-x X', '-x ' + str(self.coordinates_dict[str(account_number)][0])).replace('-y Y', '-y ' + str(self.coordinates_dict[str(account_number)][1]))
        self.log(f"Account initialized: {account.login}", 'green')
        self.log(f"Command: {accountActivationString}", 'white')
        if not testing:
            os.system(accountActivationString)
        else: self.log("Testing mode. Skipping lauching...", 'yellow')

    def ResetLogs(self):
        path = self.steamcmdpath + "\\steamapps\\common\\Counter-Strike Global Offensive Beta - Dedicated Server\\csgo\\addons\\sourcemod\\logs\\"
        for file in os.listdir(path):
            try:
                os.remove(path + file)
                self.log(f"[MONITORING] Deleted old logs", 'cyan')
            except PermissionError:
                pass
        open(path + "DropsSummoner.log", 'w', encoding= 'utf-8').close()

    def MonitorDrops(self):
        path = self.steamcmdpath + "\\steamapps\\common\\Counter-Strike Global Offensive Beta - Dedicated Server\\csgo\\addons\\sourcemod\\logs\\DropsSummoner.log"
        self.update()
        if self.serverstatus.status == 'NO':
            self.log("[MONITORING] Server stopped.", 'red')
            return
        else:
            logs = open(path, 'r', encoding= 'utf-8').read().split('\n')
            #delete empty entries in logs
            logs = [i for i in logs if i]
            new_logs = logs[len(self.last_logs):]
            self.last_logs = logs
            n = len(new_logs)
            if n>0:
                self.log(f"[MONITORING] Found {n} new logs:", 'cyan')
                self.CheckDrops(self.parent.utils.gc.worksheet('Выпадения'), new_logs)
        self.after(10000, self.MonitorDrops)

    def CheckDrops(self, sheet: gspread.Worksheet, logs: list):
        #example: L 07/26/2020 - 22:53:56: [DropsSummoner.smx] Игроку XyLiGaN<226><STEAM_1:0:558287561><> выпало [4281-0-1-4]
        for log in logs:
            self.update()
            if 'DropsSummoner' not in log or 'There is no case in the config' in log:
                self.log("Skipped log")
                continue
            log = log.split(' ')
            d1 = log[1].split('/')
            month = d1[0]
            day = d1[1]
            year = d1[2]
            date = f"{day}.{month}.{year} {log[3][:-1]}"
            player = log[6]
            player = player[:player.find('<')]
            drop = log[8]
            drop = drop.split('-')[0][1:]
            for skin in self.parent.utils.drops:
                if str(skin.dropid) == drop:
                    drop = skin
            self.log(f"Account {player} received {drop.name}  {date}", 'green')
            i = int(sheet.acell('F1').value) + 2
            sheet.update_acell(f"A{i}", player)
            sheet.update_acell(f"B{i}", drop.name)
            sheet.update_acell(f"C{i}", date)
            sheet.update_acell(f"D{i}", drop.price)
            if self.autoTrading.get():
                if not player.isdigit():
                    self.log(f"Account {player} is not digit. Cant trade", 'red')
                    continue
                self.tradestack.append(self.parent.accounts[int(player)-1])  
                self.log("Added 1 trade to stack")

    def UpdatePrices(self, index: int = 0):
        if index == 0:
            self.log('Updating drops prices...', 'yellow')
        if index >= len(self.parent.utils.drops):
            self.log('Drops updated', 'green')
            return
        self.parent.utils.drops[index].updatePrice()
        self.after(1500, self.UpdatePrices, index + 1)

    def ListAccounts(self):
        accounts = self.parent.utils.getAccounts()
        for account in accounts:
            self.parent.update()
            self.log(f"\nACCOUNT {account.number}:", 'grey')
            self.log(f"\tSteamID: {account.steamid}")
            self.log(f"\tLogin: {account.login}")
            self.log(f"\tPassword: {account.password}")
            self.log(f"\tAPI: {account.api_key}")
            self.log(f"\tSECRET: {account.shared_secret}")
            self.log(f"\tIdentity Secret: {account.identity_secret}")

    def GetLocalIP(self) -> str:
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

    def StartServer(self):
        self.last_logs = []
        self.ResetLogs()
        self.log("[SERVER] Starting server...", 'yellow')
        self.serverstatus.SetStatus('WAIT')
        Popen("srcds -game csgo -console -usercon -nobots -port 27027 -usercon -console +game_type 0 +game_mode 0 +mapgroup mg_custom +map achievement_idle +sv_logflush 1",
        cwd=self.steamcmdpath + r"\steamapps\common\Counter-Strike Global Offensive Beta - Dedicated Server", shell=True)
        self.after(2000, self.RCONConnection)

    def RCONCommand(self) -> None:
        try:
            client = self.RCON
        except:
            self.log('[SERVER] Server is not running', 'red')
            return
        if client is None:
            self.log('[SERVER] RCON is not connected', 'red')
            return
        dialog = ctk.CTkInputDialog(title = 'RCON command', text = 'Enter command')
        command = dialog.get_input()
        if command == 'exit':
            self.log('[SERVER] Server closed', 'red')
            self.serverstatus.SetStatus('NO')
            self.RCON = None
        response = client.run(command)
        self.log(f"[SERVER] {command}", 'yellow')
        self.log(f"[SERVER] {response}", 'white')

    def UpdateServer(self):
        self.log("[SERVER] Updating server...", 'yellow')
        Popen('start steamcmd.exe +login anonymous +app_update 740 validate +quit', cwd=self.steamcmdpath, shell=True)
    
    def GetRCONpassword(self) -> str:
        path = self.steamcmdpath + '\\steamapps\\common\\Counter-Strike Global Offensive Beta - Dedicated Server\\csgo\\cfg\\server.cfg'
        with open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for line in lines:
                if line.startswith('rcon_password'):
                    password = line.split(' ')[1].replace('"', '')
                    self.log('[SERVER] RCON password: ' + password, 'green')
                    break
            else:
                self.log('[SERVER] RCON password not found', 'red')
                return
        return password

    def RCONConnection(self, depth: int = 1):
        self.update()
        if depth > 10:
            self.log('[SERVER] Server is not running', 'red')
            self.serverstatus.SetStatus('NO')
            return
        try:
            client = Client(self.localip, 27027, passwd=self.GetRCONpassword())
            client.connect(login=True)
            self.log('[SERVER] Server is running', 'green')
            self.log('[SERVER] Connected to RCON', 'green')
            self.serverstatus.SetStatus('OK')
            self.RCON = client
        except ConnectionRefusedError:
            self.log(f'[SERVER] Connection refused. Retrying ({depth})', 'red')
            self.serverstatus.SetStatus('WAIT')
            self.RCONConnection(depth + 1)

    def log(self, message: str, color: str = 'white'):
        self.parent.console.Log(f"{message}", color)

class Drop():
    def __init__(self, parent, sheet: gspread.Worksheet, index: int, name: str, marketid: str, dropid: str, price: str):
        self.parent = parent
        self.sheet = sheet
        self.name = name
        self.index = index
        self.dropid = dropid
        self.marketid = marketid
        self.price = ''.join(price.split()[:-1])

    def updatePrice(self):
        try:
            req = "https://steamcommunity.com/market/priceoverview/?country=RU&currency=5&appid=730&market_hash_name=" + self.marketid
            r = requests.get(req)
            price = r.json()["lowest_price"]
            price = price.replace(" pуб.", "") # deleting " pуб." from price
            self.sheet.update_acell(f"E{self.index + 2}", price) 
            self.sheet.update_acell(f"F{self.index + 2}", datetime.now().strftime("%d.%m.%Y %H:%M:%S"))
            self.log(f"{price} руб. Updated", 'green')
        except Exception as e:
            self.log(f"Not updated", 'red')
    
    def log(self, message: str, color: str = 'white'):
        self.parent.log(f"[{self.name}] {message}", color)

class SteamAccount():
    def __init__(self, parent, number: int, steamid: str, login: str, password: str, api_key: str, shared_secret: str, identity_secret: str, status: str = 'OFF', steamPID: int = 0, csgoPID: int = 0):
        self.parent = parent
        self.number = number
        self.steamid = steamid
        self.login = login
        self.password = password
        self.api_key = api_key
        self.shared_secret = shared_secret
        self.identity_secret = identity_secret
        self.status = status
        self.steamPID = steamPID
        self.csgoPID = csgoPID

    def __repr__(self):
        return str(self.login)

    def log(self, message: str, color: str = 'white'):
        self.parent.console.Log(f'[{self.number}] {message}', color)

    def launch(self, accountActivationString: str):
        self.status = 'LAUNCHING'
        self.parent.panel.UpdateStatus(self.number, 'LAUNCHING','yellow')
        self.parent.update()
        accountActivationString = accountActivationString.replace('LOGIN', str(self.login)).replace('PASSWORD', str(self.password))
        title = 'Вход в Steam'
        print(accountActivationString)
        autoit.run(accountActivationString)
        while not autoit.win_exists(title):
            pass
        autoit.win_activate(title)
        autoit.win_wait_active(title)
        self.steamPID = autoit.win_get_process(title)
        while autoit.win_exists(title):
            try:
                sleep(3)
                autoit.win_activate(title)
                for _ in range(5):
                    autoit.send('{BACKSPACE}')
                autoit.send(generate_one_time_code(self.shared_secret))
                autoit.send("{Enter}")
            except:
                pass
            finally:
                sleep(3)
        title = f'{self.number} ACCOUNT'
        while not autoit.win_exists(title):
                autoit.win_wait('Counter-Strike: Global Offensive - Direct3D 9')
                autoit.win_activate('Counter-Strike: Global Offensive - Direct3D 9')
                autoit.win_wait_active('Counter-Strike: Global Offensive - Direct3D 9')
                autoit.win_set_title('Counter-Strike: Global Offensive - Direct3D 9', title)
        self.csgoPID = autoit.win_get_process(title)
        print(self.csgoPID, self.steamPID)
        self.status = 'LAUNCHED'
        self.parent.panel.UpdateStatus(self.number, 'LAUNCHED','green')

    def kill(self):
        self.log("Closing")
        os.system(f'taskkill /PID {self.csgoPID} /t /f')
        os.system(f'taskkill /PID {self.steamPID} /t /f')
        #os.kill(self.csgoPID, signal.SIG)
        #os.kill(self.steamPID, signal.SIGTERM)
        self.csgoPID = 0
        self.steamPID = 0
        self.status = 'DROPPED'
        self.parent.panel.UpdateStatus(self.number, 'DROPPED','blue')

    def sendTrade(self, partner: str):
        client = self.getSteamClient()
        if client is None:
            return
        items = self.getInventory()
        self.log(f'Sending trade to {partner}')
        if items is None:
            self.log('Cant send empty trade', 'red')
            return
        try:
            client.make_offer(items, [], partner, f"Trade from {self.steamid}")
            self.log('Trade sent', 'green')
        except Exception as e:
            self.log('Trade sending failed', 'red')
            self.log(e)
            return

    def getInventory(self) -> list[Asset]:
        self.log('Loading inventory...')
        data = requests.get(f'https://steamcommunity.com/inventory/{self.steamid}/730/2?l=english&count=5000')
        if data.status_code == 200: self.log('Inventory loaded', 'green')
        else:
            self.log(f'Inventory loading failed with status code: {data.status_code}', 'red')
            return
        json_data = json.loads(data.text)
        inventory_count = json_data['total_inventory_count']
        if inventory_count == 0:
            self.log('Inventory is empty', 'red')
            return
        assets = [(Asset(asset['assetid'], GameOptions('730','2'), asset['amount']), asset['classid']) for asset in json_data['assets']]
        descriptions = {description['classid']:description['tradable'] for description in json_data['descriptions']}
        tradable_assets = [asset[0] for asset in assets if descriptions[asset[1]] == 1]
        self.log(f'Inventory loaded. {len(tradable_assets)} tradable items found', 'green')
        return tradable_assets
    
    def getSteamClient(self, depth: int = 0) -> SteamClient:
        self.parent.update()
        if depth > 4:
            self.log(f'Login failed', 'red')
            return
        self.log('Logging in...')
        if self.api_key == '' or self.login == '' or self.password == '' or self.shared_secret == '':
            self.log('Login failed: Empty fields', 'red')
            return
        try:
            steam_client = SteamClient(self.api_key, self.login, self.password, self.shared_secret, self.identity_secret, self.steamid)
            steam_client.login(self.login, self.password, self.shared_secret)
            self.log('Logged in', 'green')
            self.parent.update()
            return steam_client
        except Exception as e:
            self.getSteamClient(depth + 1)
            return
    
class Utils():
    def __init__(self, app):
        self.app = app
        self.config = self.connectConfig()
        self.gc = self.connectServiceAccount()

        self.sheet = self.gc.worksheet('Дропы')
        self.drops = self.getDrops()
    
    def getDrops(self):
        self.log("Loading drops")
        data = self.sheet.get_all_records()
        self.log(f"{len(data)} drops loaded", 'green')
        return [Drop(self, self.sheet, i, data[i]['Название'], data[i]['MarketID'], data[i]['DropID'], data[i]['Цена']) for i in range(len(data))]

    def log(self, message: str, color: str = 'white'):
        self.app.console.Log(message, color)
    
    def getSteamCMDpath(self) -> str:
        self.log("Looking for SteamCMD installation", 'yellow')
        self.app.options.steamcmdstatus.SetStatus('WAIT')
        drives = [ chr(x) + ":" for x in range(65,91) if os.path.exists(chr(x) + ":") ]
        steamcmdpath = ''
        for drive in drives:
            i = 0
            for r,d,f in os.walk(drive + '\\'):
                i+=1
                if i%100==0:
                    self.log(f"Looking for SteamCMD at {r}")
                self.app.update()
                if 'steamcmd' not in r.lower(): continue
                if 'steamcmd.exe' in f:
                    steamcmdpath = r
                    break
        self.log(f"SteamCMD found at: {steamcmdpath}\\steamcmd.exe", 'green')
        self.app.options.steamcmdstatus.SetStatus('OK')
        return steamcmdpath
    
    def getSteampath(self) -> str:
        self.log("Looking for Steam installation", 'yellow')
        self.app.options.steamstatus.SetStatus('WAIT')
        possiblePaths = [r"X:\Steam\steam.exe", r"X:\Program Files\Steam\steam.exe", r"X:\Program Files (x86)\Steam\steam.exe"]
        validPaths = []
        Drives = [ chr(x) for x in range(65,91) if os.path.exists(chr(x) + ":") ]
        for Drive in Drives:
            for path in possiblePaths:
                self.app.update()
                path = path.replace("X", Drive)
                self.log(f"Looking for Steam at {path}")
                if os.path.exists(path):
                    validPaths.append(path)
        if len(validPaths) == 0:
            self.app.options.steamstatus.SetStatus('NO')
            self.log("Steam not found. Please enter path to steam.exe", 'red')
            return
        elif len(validPaths) == 1:
            steamPath = validPaths[0]
            self.log(f"Steam found at {steamPath}", 'green')
        else:
            self.log("Steam found at multiple locations:", 'yellow')
            for i in range(len(validPaths)):
                self.log(f"{i+1}. {validPaths[i]}", 'white')
                return validPaths[0]
        self.app.options.steamstatus.SetStatus('OK')
        return steamPath
    
    def connectServiceAccount(self) -> gspread.Client:
        config = open('config.json', 'r')
        config = json.load(config)
        setPath = config['serviceAccountPath']
        if setPath != '': setPath += '\\'
        try:
            gc = gspread.service_account()
            self.log("Service account file loaded.", 'green')
            self.app.options.servicestatus.SetStatus('OK')
            return gc.open('Ферма')
        except FileNotFoundError:
            self.log("Service account is not set up", 'red')
            servicePath = f'{setPath}service_account.json'
            self.log(servicePath)
            if os.path.exists(servicePath):
                self.app.options.servicestatus.SetStatus('WAIT')
                self.log("Service account file found.", 'green')
                self.log("Creating gspread folder")
                appdata = os.getenv('APPDATA')
                path = appdata + '\\gspread'
                self.log("Moving service account file to {}".format(path), 'yellow')
                os.makedirs(path, exist_ok=True)
                os.rename(servicePath,f"{path}\\service_account.json")
                gc = gspread.service_account()
                self.log("Service account file loaded.", 'green')
                self.app.options.servicestatus.SetStatus('OK')
                return gc.open('Ферма')
            else:
                self.log("Service account file not found.", 'red')
                self.log("Please download service account file and put it in the same folder or specify the path", 'red')
                self.app.options.servicestatus.SetStatus('NO')

    def connectConfig(self) -> dict:
        try:
            data = open('config.json', 'r')
            self.log("Config file loaded.", 'green')
            data = json.loads(data.read())
            availableData = {}
            if data['cmdcommand'] != '':
                availableData['cmdcommand'] = data['cmdcommand']
            if data['steamcmdpath'] != '' and os.path.exists(data['steamcmdpath'] + '\\steamcmd.exe'):
                availableData['steamcmdpath'] = data['steamcmdpath']
                self.app.options.steamcmdstatus.SetStatus('OK')
            else:
                self.app.options.steamcmdstatus.SetStatus('NO')
            if data['steampath'] != '' and os.path.exists(data['steampath']):
                availableData['steampath'] = data['steampath']
                self.app.options.steamstatus.SetStatus('OK')
            else:
                self.app.options.steamstatus.SetStatus('NO')
            self.config = data
            self.app.options.configstatus.SetStatus('OK')
            return availableData
        except FileNotFoundError:
            self.app.options.configstatus.SetStatus('WAIT')
            self.log("Config file is not set up", 'red')
            self.log("Creating config file...", 'yellow')
            data = open('config.json', 'w')  
            steamcmdpath = self.getSteamCMDpath()
            steampath = self.getSteampath()
            data.write(json.dumps({"serviceAccountPath": "", "steamcmdpath": steamcmdpath, "steampath": steampath, "cmdcommand": "STEAMPATH -login LOGIN PASSWORD -language russian -applaunch 730 -low -nohltv -nosound -novid -window -w 640 -h 480 +connect IP -console +exec farm.cfg -x X -y Y"}))
            data.close()
            self.log("Config file loaded.", 'green')
            self.app.options.configstatus.SetStatus('OK')
            return self.connectConfig()
        
    def getAccounts(self) -> list[SteamAccount]:
        self.log("Getting accounts from Google Sheets", 'yellow')
        accounts = self.gc.sheet1.get_all_records()
        accounts = [SteamAccount(self.app, account['Номер'], str(account['SteamID']), account['Логин'], account['Пароль'], account['API'], account['SECRET'], account['IDENTITY']) for account in accounts]
        self.log(f"Loaded {len(accounts)} accounts", 'green')
        self.app.update()
        return accounts
    
    def validateAccounts(self, accounts: list[SteamAccount], current: int = 0, invalid: int = 0):
        if current == 0:
            self.log("Checking accounts", 'yellow')
        if current >= len(accounts):
            self.log("Checked all accounts", 'green')
            self.log(f"Found {invalid} invalid accounts", 'red' if invalid > 0 else 'green')
            return
        client = accounts[current].getSteamClient()
        if client is None:
            self.validateAccounts(accounts, current+1, invalid+1)
            return
        self.app.after(60000, self.validateAccounts, accounts, current+1, invalid)



def main():
    application = App()
    application.mainloop()

if __name__ == '__main__':
    main()
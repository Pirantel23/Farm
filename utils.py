import gspread
from glob import glob
from json import load
from time import sleep

def getIndexByLogin(login: str) -> int:
    for account in accounts:
        if account['Логин'] == login:
            return int(account['Номер'])

def setupAccounts():
    global accounts
    gc = gspread.service_account().open('Ферма').sheet1
    accounts = gc.get_all_records()
    for file in glob('*.maFile'):
        with open(file, 'r', encoding='utf-8') as data:
            info = load(data)
            login = info['account_name']
            number = getIndexByLogin(login)
            if number is None: continue
            account = accounts[number-1]
            print(info)
            if not account['SteamID']:
                print('Writing steamid')
                steamid = file[:file.find('.')]
                gc.update_acell(f'B{number+1}', steamid)
                sleep(0.2)
            if not account['Код']:
                print('Writing revocation code')
                code = info['revocation_code']
                gc.update_acell(f'F{number+1}', code)
                sleep(0.2)
            if not account['SECRET']:
                print('Writing SECRET')
                secret = info['shared_secret']
                gc.update_acell(f'H{number+1}', secret)
                sleep(0.2)
            if not account['IDENTITY']:
                print('Writing IDENTITY')
                identity = info['identity_secret']
                gc.update_acell(f'I{number+1}', identity)
                sleep(0.2)


setupAccounts()
print('Finished')
input('Press any key to exit...')
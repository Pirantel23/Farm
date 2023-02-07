import os
    
os.system(r'pyinstaller --noconfirm --windowed --uac-admin --icon icon.ico --onefile --add-data "C:\Users\gore\AppData\Roaming\Python\Python311\site-packages\customtkinter;customtkinter" main.py')
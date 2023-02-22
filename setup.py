import os
    
os.system(r'pyinstaller --noconfirm --uac-admin --icon icon.ico --onefile --add-data "C:\Users\Pirantel\AppData\Local\Programs\Python\Python311\Lib\site-packages\autoit\lib\AutoItX3_x64.dll;autoit\lib" --add-data "C:\Users\Pirantel\AppData\Local\Programs\Python\Python311\Lib\site-packages\customtkinter;customtkinter" application.py')
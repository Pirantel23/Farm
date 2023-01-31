import PyInstaller.__main__
import os
    
PyInstaller.__main__.run([  
     'main.py',
     '--onefile',
     '--uac-admin',
     '-i=icon.ico'                                 
])
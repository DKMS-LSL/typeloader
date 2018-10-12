'''
Created on 03.09.2018

@author: schoene
'''
import sys, os
from cx_Freeze import setup, Executable

# remove dummy table files
for myfile in os.listdir("tables"):
    if "dummy" in myfile:
        os.remove(os.path.join("tables", myfile))


build_exe_options = {"includes": ["authuser", "typeloader_core"],
                     "include_files": ["config_raw.ini", 'icons/', 'tables/', 'reference_data/', 'blastn/', "LICENSE.txt"],
                     "excludes": ["tkinter"]}

base = None
if sys.platform == "win32":
    base = "Win32GUI"
    
setup(name = "TypeLoader",
      version = "2.0.1",
      description = "TypeLoader",
      options = {"build_exe": build_exe_options},
      executables = [Executable("typeloader_GUI.pyw", 
                                base = base, 
                                icon = os.path.join("icons", "TypeLoader.ico"),
                                targetName = "TypeLoader.exe")])
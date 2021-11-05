#!/usr/bin/env python3
# -*- coding: cp1252 -*-
'''
Created on 03.09.2018

builds the TypeLoader executable for Windows using cx_Freeze

@author: schoene
'''
import sys, os
from cx_Freeze import setup, Executable

# remove dummy table files
for myfile in os.listdir("tables"):
    if "dummy" in myfile:
        os.remove(os.path.join("tables", myfile))

build_exe_options = {"includes": ["authuser",
                                  "typeloader_core",
                                  ],
                     "include_files": ["config_raw.ini",
                                       "config_base.ini",
                                       "config_company.ini",
                                       "LICENSE.txt",
                                       "sound_done.mp3",
                                       'icons/',
                                       'tables/',
                                       'blastn/',
                                       "sample_files/",
                                       "ENA_Webin_CLI/",
                                       ],
                     "excludes": ["tkinter",
                                  "unittest",
                                  ]}

base = None
if sys.platform == "win32":
    base = "Win32GUI"

setup(name="TypeLoader",
      version="2.11.0",
      description="TypeLoader",
      options={"build_exe": build_exe_options},
      executables=[Executable("typeloader_GUI.pyw",
                              base=base,
                              icon=os.path.join("icons", "TypeLoader.ico"),
                              targetName="TypeLoader.exe")]
      )

#!/usr/bin/env python3
# -*- coding: cp1252 -*-
'''
Created on ?

GUI_stylesheet.py

defined stylesheet info for a consistent color scheme in line with DKMS CI

@author: Bianca Schoene
'''

color_dic = {"DKMSred" : "#E2001A",
             "DKMSyellow" : "#FDDB00",
             "DKMSpurple" : "#743BBC",
             "DKMSblue" : "#00A2E1",
             "DKMSgreen" : "#78D64A",
             "DKMSlightpink" : "#F59BA5",
             "DKMSpink" : "#ED6676",
             "DKMSdarkpink" : "#E53449",
             "grey" : "#C0C0C0",
             "white" : "#FFFFFF"}

app_stylesheet = """
    QStatusBar {background: DKMSred; color: white}
    QMenuBar {background: DKMSred; color: white}
    QTextEdit {font: 10 pt "Courier"}
    """
    
def make_stylesheet():
    global app_stylesheet
    for name in color_dic:
        app_stylesheet = app_stylesheet.replace(name, color_dic[name])
    return app_stylesheet


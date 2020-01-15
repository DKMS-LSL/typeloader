#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GUI_user_manual.py

allow the user to access the user manual
"""
import sys, os

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, 
                             QLabel, QApplication)
from PyQt5.QtGui import QIcon

import general

from __init__ import __version__

#===========================================================
# classes:

class UserManualDialog(QDialog):
    """a dialog to download example files
    """
    def __init__(self, log, parent = None):
        super().__init__(parent)
        self.log = log
        self.setWindowTitle("Access TypeLoader's User Manual")
        self.setWindowIcon(QIcon(general.favicon))
        self.resize(250,50)
        self.init_UI()
        self.setModal(True)
        self.show()
        
    def init_UI(self):
        """establish and fill the UI
        """
        self.log.info("Showing User Manual Link...")
        layout = QVBoxLayout(self)
        self.setLayout(layout)
        
        lbl_text = "View the TypeLoader User Manual on GitHub (online)"
        user_manual_url = "https://github.com/DKMS-LSL/typeloader/blob/master/user_manual/_main.md"
        lbl = QLabel('<a href="{}">{}</a>'.format(user_manual_url, lbl_text))
        lbl.setStyleSheet(general.label_style_normal)
        lbl.setOpenExternalLinks(True)
        layout.addWidget(lbl)
        
pass
#===========================================================
# functions:

pass    
#===========================================================
# main:


def main():
    log = general.start_log(level="DEBUG")
    log.info("<Start {} V{}>".format(os.path.basename(__file__), __version__))
    app = QApplication(sys.argv)
    
    ex = UserManualDialog(log)
    ex.show()#Maximized()
    result = app.exec_()
    
    log.info("<End>")
    sys.exit(result)


if __name__ == '__main__':
    main()

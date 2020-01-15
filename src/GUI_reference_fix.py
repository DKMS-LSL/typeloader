#!/usr/bin/env python3
# -*- coding: cp1252 -*-
'''
Created on ?

GUI_reference_fix.py

a QDialog to replace a broken IPD release with an older working version

@author: Bianca Schoene
'''

from PyQt5.QtWidgets import (QDialog, QFileDialog, QFormLayout,
                             QLabel, QApplication)
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtGui import QIcon

import sys, os
from shutil import copyfile

import general

from __init__ import __version__
from PyQt5.Qt import QPushButton, QMessageBox


#===========================================================
# classes:

class ReferenceFixingDialog(QDialog):
    """a dialog to replace a broken IPD release with an older working version
    """
    def __init__(self, settings, log, parent = None):
        super().__init__(parent)
        self.settings = settings
        self.log = log
        self.setWindowTitle("Replace broken IPD release")
        self.setWindowIcon(QIcon(general.favicon))
        self.resize(200,50)
        self.init_UI()
        self.setModal(True)
        self.show()
        
    def init_UI(self):
        """establish and fill the UI
        """
        layout = QFormLayout(self)
        self.setLayout(layout)
        
        self.btn_dic = {}
        
        lbl = QLabel("Does either of the current IPD releases seem broken and you want to\nswitch to an older, non-broken version?")
        lbl.setStyleSheet(general.label_style_italic)
        layout.addRow(lbl)
        
        msg = "Clicking this button will download an older, non-broken release from IPD and TypeLoader will then use it as its reference."
        
        layout.addRow(QLabel(""))
        hla_btn = QPushButton("Replace with trusted version!", self)
        self.btn_dic[hla_btn] = ("HLA")
        hla_btn.clicked.connect(self.ask_confirmation)
        hla_lbl = QLabel("HLA and MIC:")
        hla_lbl.setStyleSheet(general.label_style_2nd)
        hla_lbl.setWhatsThis(msg.format("HLA"))
        hla_btn.setWhatsThis(msg.format("HLA"))
        layout.addRow(hla_lbl, hla_btn)
        
        kir_btn = QPushButton("Replace with trusted version!", self)
        self.btn_dic[kir_btn] = ("KIR")
        kir_btn.clicked.connect(self.ask_confirmation)
        kir_lbl = QLabel("KIR:")
        kir_lbl.setStyleSheet(general.label_style_2nd)
        kir_lbl.setWhatsThis(msg.format("KIR"))
        kir_btn.setWhatsThis(msg.format("KIR"))
        layout.addRow(kir_lbl, kir_btn)
    
    
    @pyqtSlot()  
    def ask_confirmation(self):
        """asks for user confirmation before proceeding
        """
        (target_family) = self.btn_dic[self.sender()]
        confirm_msg = "Are you sure you want to replace TypeLoader's current IPD database for {} with an older but trusted version?".format(target_family)
        self.log.debug(confirm_msg)
        reply = QMessageBox.question(self, 'Are you sure?', confirm_msg,                     
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.log.debug("\t=> User confirmed.")
            self.replace_new_version_with_trusted(target_family)
        else:
            self.log.debug("\t=> User decided not to.")
            
            
    def replace_new_version_with_trusted(self, target_family):
        """downloads trusted version of database and creates new db files from it
        """
        self.log.info("Replacing broken {} version with trusted older version...".format(target_family))

        
        
pass
#===========================================================
# functions:

def log_uncaught_exceptions(cls, exception, tb):
    """reimplementation of sys.excepthook;
    catches uncaught exceptions, logs them and exits the app
    """
    import traceback
    from PyQt5.QtCore import QCoreApplication
    log.critical('{0}: {1}'.format(cls, exception))
    log.exception(msg = "Uncaught Exception", exc_info = (cls, exception, tb))
    #TODO: (future) maybe find a way to display the traceback only once, both in console and logfile?
    sys.__excepthook__(cls, exception, traceback)
    QCoreApplication.exit(1) 
    
pass    
#===========================================================
# main:


def main():
    import GUI_login
    log = general.start_log(level="DEBUG")
    log.info("<Start {} V{}>".format(os.path.basename(__file__), __version__))
    settings_dic = GUI_login.get_settings("admin", log)
    app = QApplication(sys.argv)
    sys.excepthook = log_uncaught_exceptions
    
    ex = ReferenceFixingDialog(settings_dic, log)
    ex.show()
    result = app.exec_()
    
    log.info("<End>")
    sys.exit(result)


if __name__ == '__main__':
    main()

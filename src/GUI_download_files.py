#!/usr/bin/python3
# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import (QDialog, QFileDialog, QVBoxLayout, 
                             QLabel, QApplication)
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtGui import QIcon

import sys, os
from shutil import copyfile

import general

from __init__ import __version__
from PyQt5.Qt import QPushButton


#===========================================================
# classes:

class ExampleFileDialog(QDialog):
    """a dialog to download example files
    """
    def __init__(self, settings, log, parent = None):
        super().__init__(parent)
        self.settings = settings
        self.log = log
        self.setWindowTitle("Download example files")
        self.setWindowIcon(QIcon(general.favicon))
        self.resize(200,50)
        self.init_UI()
        self.setModal(True)
        self.show()
        
    def init_UI(self):
        """establish and fill the UI
        """
        layout = QVBoxLayout(self)
        self.setLayout(layout)
        
        lbl = QLabel("Download example files")
        lbl.setStyleSheet(general.label_style_2nd)
        layout.addWidget(lbl)
        
        ipd_lbl = QLabel("For IPD submission:")
        ipd_lbl.setStyleSheet(general.label_style_normal)
        layout.addWidget(ipd_lbl)
        
        pretypings_btn = QPushButton("Pretypings File", self)
        pretypings_btn.clicked.connect(self.download_pretypings)
        pretypings_btn.setWhatsThis("This file contains a list of previously identified alleles for all loci for each sample to be submitted to IPD")
        layout.addWidget(pretypings_btn)
        
    @pyqtSlot()
    def download_pretypings(self):
        """download example pretypings file
        """
        self.log.debug("Downloading example pretypings file...")
        myfile = os.path.join("sample_files", "pretypings_example.csv")
        suggested_path = os.path.join(self.settings["default_saving_dir"], myfile)
        chosen_path = QFileDialog.getSaveFileName(self, "Download example pretypings file...", suggested_path)[0]
        if chosen_path:
            copyfile(myfile, chosen_path)
        
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
    
    ex = ExampleFileDialog(settings_dic, log)
#     ex = PasswordEditor(settings_dic, log)
    ex.show()#Maximized()
    result = app.exec_()
    
    log.info("<End>")
    sys.exit(result)


if __name__ == '__main__':
    main()
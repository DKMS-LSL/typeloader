#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
Created on 15.07.2020

GUI_mini_dialogs.py

contains various small TypeLoader dialogs

@author: Bianca Schoene
'''

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QLabel, QApplication)
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtGui import QIcon
from PyQt5.Qt import QPushButton, QMessageBox

import sys, os, shutil
from shutil import copyfile

import general
from GUI_login import handle_reference_update


# ===========================================================
# classes:


# ===========================================================
# functions:

def log_uncaught_exceptions(cls, exception, tb):
    """reimplementation of sys.excepthook;
    catches uncaught exceptions, logs them and exits the app
    """
    import traceback
    from PyQt5.QtCore import QCoreApplication
    log.critical('{0}: {1}'.format(cls, exception))
    log.exception(msg="Uncaught Exception", exc_info=(cls, exception, tb))
    # TODO: (future) maybe find a way to display the traceback only once, both in console and logfile?
    sys.__excepthook__(cls, exception, traceback)
    QCoreApplication.exit(1)


pass


# ===========================================================
# main:


def main():
    import GUI_login
    log = general.start_log(level="DEBUG")
    log.info("<Start {}>".format(os.path.basename(__file__)))
    settings_dic = GUI_login.get_settings("admin", log)
    app = QApplication(sys.argv)
    sys.excepthook = log_uncaught_exceptions

    result = app.exec_()

    log.info("<End>")
    sys.exit(result)


if __name__ == '__main__':
    main()

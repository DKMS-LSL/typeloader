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


class RefreshReferenceDialog(QDialog):
    """a dialog to allow manually refreshing the reference database
    """
    def __init__(self, settings, log, parent=None, testing=False):
        super().__init__(parent)
        self.settings = settings
        self.log = log
        if testing:
            self.parent = None
        else:
            self.parent = parent
        self.btn_dic = {}
        self.updated = []
        self.log.info("Opened RefreshReferenceDialog")

        self.setWindowTitle("Refresh reference")
        self.setWindowIcon(QIcon(general.favicon))
        self.resize(300, 100)
        self.init_UI()
        self.setModal(True)
        self.show()

    def init_UI(self):
        """establish and fill the UI
        """
        layout = QVBoxLayout(self)
        self.setLayout(layout)

        msg = "Would you like to re-create any of TypeLoader's reference files?\n"
        msg += "(This will take a minute or so. Please wait after clicking.)\n"
        layout.addWidget(QLabel(msg))

        for text in ["HLA", "KIR", "Both"]:
            btn = QPushButton(text, self)
            btn.clicked.connect(self.update_reference)
            self.btn_dic[text] = btn
            layout.addWidget(btn)

    @pyqtSlot()
    def update_reference(self):
        """catches button clicked and updates reference accordingly
        """
        text = self.sender().text()
        if text in ["HLA", "KIR"]:
            update_me = [text]
        elif text == "Both":
            update_me = ["HLA", "KIR"]

        self.log.info(f"User chose to update {' and '.join(update_me)}.")
        blast_path = self.settings["blast_path"]
        reference_local_path = os.path.join(self.settings["root_path"],
                                            self.settings["general_dir"],
                                            self.settings["reference_dir"])

        self.updated = handle_reference_update(update_me, reference_local_path, blast_path, self.parent, self.log)
        self.close()


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

    ex = RefreshReferenceDialog(settings_dic, log)
    ex.show()
    result = app.exec_()

    log.info("<End>")
    sys.exit(result)


if __name__ == '__main__':
    main()

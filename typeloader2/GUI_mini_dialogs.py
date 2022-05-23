#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
Created on 15.07.2020

GUI_mini_dialogs.py

contains various small TypeLoader dialogs

@author: Bianca Schoene
'''

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QFormLayout,
                             QLabel, QLineEdit, QApplication, QInputDialog)
from PyQt5.QtCore import pyqtSlot, pyqtSignal
from PyQt5.QtGui import QIcon
from PyQt5.Qt import QPushButton, QMessageBox

import sys, os, shutil
from shutil import copyfile

import general
from GUI_login import handle_reference_update
from typeloader_functions import perform_reference_update, update_curr_versions


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
            btn.setCheckable(True)
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

        self.updated = handle_reference_update(update_me, reference_local_path, blast_path,
                                               self.parent, self.settings, self.log)
        self.sender().setChecked(False)
        self.close()


class ResetReferenceDialog(QDialog):
    """a dialog to allow manually resetting a reference database to a previous version
    """
    db_reset_done = pyqtSignal(bool)

    def __init__(self, settings, log, parent=None, testing=False, target_value=None):
        super().__init__(parent)
        self.settings = settings
        self.log = log
        if testing:
            self.parent = None
        else:
            self.parent = parent
        self.testing = testing
        self.target_value = target_value
        self.btn_dic = {}
        self.updated = []
        self.log.debug("Opened ResetReferenceDialog")

        self.setWindowTitle("Reset reference to arbitrary version")
        self.setWindowIcon(QIcon(general.favicon))
        self.resize(300, 100)
        self.init_UI()
        self.setModal(True)
        self.show()

    def init_UI(self):
        """establish and fill the UI
        """
        layout = QFormLayout(self)
        self.setLayout(layout)

        msg = "Would you like to reset any of TypeLoader's reference files to an earlier version?\n"
        msg += "(This will take a minute or so. Please wait after clicking.)\n"
        layout.addRow(QLabel(msg))

        msg2 = "This will affect all users and may have unintended side effects!\nUse with care!"
        lbl2 = QLabel(msg2)
        lbl2.setStyleSheet(general.label_style_2nd)
        layout.addRow(lbl2)

        self.version_field = QLineEdit(self)
        self.version_field.setWhatsThis("Enter any valid version of the target, e.g., '3.39.0' or '2.7.1'.")
        if self.target_value:
            self.version_field.setText(self.target_value)
        layout.addRow(QLabel("Target version:"), self.version_field)

        for text in ["HLA", "KIR"]:
            btn = QPushButton(text, self)
            btn.setCheckable(True)
            btn.clicked.connect(self.update_reference)
            self.btn_dic[text] = btn
            layout.addRow(btn)

    def check_proceed(self, db_name):
        """ check whether version is

        """
        if not self.testing:
            reply = QMessageBox.question(self, "Are you sure?",
                                         f"This will reset the TypeLoader {db_name.upper()} reference for ALL your "
                                         f"users!\nAre you sure you want to proceed?",
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No
                                         )
            if reply == QMessageBox.No:
                self.close()
                return False, "User chose to abort."

            pwd, ok = QInputDialog.getText(self, "Enter Password", "Please provide password:", QLineEdit.Password)
            if ok:
                if pwd != "ichdarfdas":
                    return False, "Wrong password!"
            else:
                return False, "Could not get password!"

        return True, None

    def handle_version_input(self, version):
        if not version:
            return False, "Missing version", "Please insert a version number, e.g., 3.39.0!"

        dots = version.count(".")
        version = version.replace(".", "").replace("-", "").replace("_", "")

        try:
            int(version)
        except ValueError:
            return False, "Invalid version", \
                   "Version should only contain digits and up to 2 dots, like '2.7.0' or '3.39'!"

        if not version.endswith("0") and dots < 2:
            version += "0"
        return True, version, None

    @pyqtSlot()
    def update_reference(self):
        """catches button clicked and updates reference accordingly
        """
        db_name = self.sender().text().lower()
        version = self.version_field.text().strip()

        proceed, msg = self.check_proceed(db_name)
        if not proceed:
            self.log.info(f"\t{msg}")
            return

        version_ok, version, msg = self.handle_version_input(version)
        if not version_ok:
            QMessageBox.warning(self, version, msg)
            return

        self.log.info(f"User chose to reset {db_name.upper()} to version {version}.")
        blast_path = self.settings["blast_path"]
        reference_local_path = os.path.join(self.settings["root_path"],
                                            self.settings["general_dir"],
                                            self.settings["reference_dir"])

        success, err_type, msg = perform_reference_update(db_name, reference_local_path, blast_path,
                                                          self.settings["proxy"], self.log,
                                                          version=version)
        self.log.info(msg.replace("\n", " "))
        if success:
            self.updated = version
            update_curr_versions(self.settings, self.log)

            msg2 = "Once you are done, please reset the reference back to the latest version, " \
                   "either manually or by restarting TypeLoader!"
            if not self.testing:
                QMessageBox.information(self, "Database reset successfull", msg)
                QMessageBox.information(self, "Please remember...", msg2)
            self.db_reset_done.emit(True)

        else:
            self.log.info("Database reset failed.")
            if not self.testing:
                QMessageBox.information(self, "Database reset failed", msg)
            self.db_reset_done.emit(False)

        self.close()


class VersionDialog(QDialog):
    """a dialog to show the current versions used by TypeLoader
    """

    def __init__(self, settings, log, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.log = log
        update_curr_versions(self.settings, self.log)
        self.parent = parent
        self.TL_version = general.read_package_variable("__version__")
        self.log.debug("Opened VersionDialog")

        self.setWindowTitle("TypeLoader's current versions")
        self.setWindowIcon(QIcon(general.favicon))
        self.resize(350, 150)
        self.init_UI()
        self.setModal(True)
        self.show()

    def init_UI(self):
        """establish and fill the UI
        """
        layout = QFormLayout(self)
        self.setLayout(layout)

        header = QLabel("Current versions:")
        header.setStyleSheet(general.label_style_2nd)
        layout.addRow(header)

        layout.addRow(QLabel(""))  # empty line

        layout.addRow(QLabel("HLA/IMGT database:"),
                      QLabel(self.settings["db_versions"]["HLA"]))

        layout.addRow(QLabel("IPD-KIR database:"),
                      QLabel(self.settings["db_versions"]["KIR"]))

        layout.addRow(QLabel("TypeLoader:"),
                      QLabel(self.TL_version))


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

    ex = VersionDialog(settings_dic, log)
    ex.show()
    result = app.exec_()

    log.info("<End>")
    sys.exit(result)


if __name__ == '__main__':
    main()

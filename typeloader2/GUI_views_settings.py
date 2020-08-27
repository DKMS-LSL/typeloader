#!/usr/bin/env python3
# -*- coding: cp1252 -*-
'''
Created on ?

GUI_views_settings.py

classes involved in building the SettingsView for Typeloader

@author: Bianca Schoene
'''

from PyQt5.QtWidgets import (QDialog, QFormLayout, QLineEdit,
                             QTabWidget, QVBoxLayout, QWidget, QMessageBox,
                             QLabel, QApplication, QComboBox)
from PyQt5.QtCore import pyqtSignal, pyqtSlot
from PyQt5.QtGui import QIcon

import sys, os, re
from configparser import ConfigParser

from authuser import user
import general
from GUI_misc import ConfirmResetWidget
from GUI_forms import ProceedButton


from PyQt5.Qt import QPushButton


#===========================================================
# classes:

class PasswordEditor(QDialog):
    """a dialog to edit a user's password
    """
    def __init__(self, settings, log, parent = None):
        super().__init__(parent)
        self.log = log
        self.log.info("Opening PasswordEditor...")
        self.settings = settings
        self.login = settings["login"]
        pickle_file = os.path.join(settings["root_path"], settings["general_dir"], "user.pickle")
        self.user_db = user.User(pickle_file)
        self.init_UI()
        self.setModal(True)
        self.show()
        
    def init_UI(self):
        layout = QFormLayout(self)
        self.setLayout(layout)
        
        lbl = QLabel("Change your password")
        lbl.setStyleSheet(general.label_style_main)
        layout.addRow(lbl)
         
        self.user_field = QLineEdit(self.login, self)
        self.user_field.setReadOnly(True)
        layout.addRow(QLabel("User Name:"), self.user_field)
         
        self.old_pw_field = QLineEdit()
        self.old_pw_field.setEchoMode(QLineEdit.Password)
        layout.addRow(QLabel("Old Password:"), self.old_pw_field)
         
        self.new_pw_field = QLineEdit()
        self.new_pw_field.setEchoMode(QLineEdit.Password)
        layout.addRow(QLabel("New Password:"), self.new_pw_field)
         
        self.new_pw_field2 = QLineEdit()
        self.new_pw_field2.setEchoMode(QLineEdit.Password)
        layout.addRow(QLabel("New Password (confirm):"), self.new_pw_field2)
        
        items = [self.new_pw_field, self.new_pw_field2]
        self.ok_btn = ProceedButton("Save new Password", items, self.log)
        for field in items:
            field.textChanged.connect(self.ok_btn.check_ready)
        self.ok_btn.clicked.connect(self.change_password)
        layout.addRow(self.ok_btn)
    
    @pyqtSlot()
    def change_password(self):
        """change the user's password
        """
        self.log.info("Attempting password change...")
        
        self.log.info("\tChecking new password against its confirmation...")
        new_pw = self.new_pw_field.text().strip()
        new_pw2 = self.new_pw_field2.text().strip()
        if new_pw != new_pw2:
            QMessageBox.warning(self, "Confirmation Error", "New password does not match its confirmation. Please try again!")
            self.new_pw_field.setText("")
            self.new_pw_field2.setText("")
            self.log.info("\t\t=> Passwords do not match! Aborting.")
            return
        
        self.log.info("\tChecking current password...")
        old_pw = self.old_pw_field.text().strip()
        old_pw_ok = self.user_db.authenticate_user(self.login, old_pw)
        if not old_pw_ok:
            QMessageBox.warning(self, "Password Error", "Your old password was wrong. Please try again!")
            self.old_pw_field.setText("")
            self.new_pw_field2.setText("")
            self.log.info("\t\t=> Password wrong! Aborting.")
            return
        
        self.log.info("\tAsking confirmation...")
        reply = QMessageBox.question(self, 'Sure?',
            "Are you sure you want to change your password?", QMessageBox.Yes | 
            QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            self.log.info("\t\t=> Confirmed.")
            self.user_db.modify_user(self.login, new_pw)
            self.log.info("\t\t=> Password changed.")
            self.close()
        else:
            self.log.info("\t\t=> No. Aborting.")
            self.ok_btn.setChecked(False)
        
    def closeEvent(self, event):
        self.log.info("Closing PasswordEditor")
        event.accept()
        

class SettingTab(QTabWidget):
    """a TabWidget to show all settings
    """
    content_changed = pyqtSignal()
    
    def __init__(self, log, cf, parent = None):
        super().__init__()
        if parent:
            self.settings = parent.settings
        else:
            import GUI_login
            self.settings = GUI_login.get_settings("admin", log)
        self.cf = cf
        self.log = log
        self.prepare_settings()
        self.init_UI()
        
    def prepare_settings(self):
        """prepares self.mydic with information about each setting
        (section, lbl_text and hint; later the responsible fields will be stored as "field")
        """
        self.mydic = {"login": {"section" : "User",
                                "lbl_text" : "Login",
                                "hint" : "User name of this account (cannot be changed!)"},
                      "user_name": {"section" : "User",
                                    "lbl_text" : "Full Name",
                                    "hint": "Your full name (stored for every project)"},
                      "short_name" : {"section" : "User",
                                    "lbl_text" : "Initials",
                                    "hint": "Used in project names"},
                      "email" : {"section" : "User",
                                 "lbl_text" : "Email Address",
                                 "hint": "Used in generated IMGT files"},
                      "address_form" : {"section" : "User",
                                        "lbl_text" : "Form of Address",
                                        "hint": "Used in generated IMGT files"},
                      
                      "xml_center_name" : {"section" : "Company",
                                           "lbl_text" : "Company Name (for ENA)",
                                           "hint": "Used in all ENA communication"},
                      "lab_of_origin" : {"section" : "Company",
                                         "lbl_text" : "Company Name (for IPD)",
                                         "hint" : "Used in all IPD communication"},
                      "lab_contact_address" : {"section" : "Company",
                                             "lbl_text" : "Lab Contact's Form of Address",
                                             "hint": "Your lab's IPD contact's form of address"},
                      "lab_contact" : {"section" : "Company",
                                       "lbl_text" : "Lab Contact for IPD",
                                       "hint": "Your lab's contact person for IPD submissions"},
                      "lab_contact_email" : {"section" : "Company",
                                             "lbl_text" : "Lab Contact Email",
                                             "hint": "Your lab's IPD contact's email address"},
                      "submittor_id" : {"section" : "Company",
                                        "lbl_text" : "IPD Submittor ID",
                                        "hint": "Your or your lab's IPD contact's IPD submittor ID"},
                      "ipd_shortname" : {"section" : "Company",
                                    "lbl_text" : "Company Shortname (for IPD files)",
                                    "hint": "used in IPD submission filenames. Use only letters or hyphens."},
                      "cell_line_token" : {"section" : "Company",
                                           "lbl_text" : "Cell line identifier",
                                        "hint": "A short identifier for your company to use for cell line naming. An acronym etc. is ideal. Use only letters or hyphens."},
                      "ftp_user" : {"section" : "Company",
                                    "lbl_text" : "FTP user",
                                    "hint": "user for FTP submission to ENA"},
                      "ftp_pwd" : {"section" : "Company",
                                   "lbl_text" : "FTP Password",
                                   "hint": "password for FTP submission to ENA"},
                      "proxy" : {"section" : "Company",
                                 "lbl_text" : "Proxy Server (if needed)",
                                 "hint": "your lab's proxy server to get beyond your firewall; may not be needed!"},
                      
                      "material_available" : {"section" : "Method",
                                              "lbl_text" : "Material Available",
                                              "hint": "Used in generated IMGT files"},
                      "primary_sequencing" : {"section" : "Method",
                                              "lbl_text" : "Primary Sequencing Technology",
                                              "hint": "Used in generated IMGT files"},
                      "secondary_sequencing" : {"section" : "Method",
                                                "lbl_text" : "Secondary Sequencing Technology",
                                                "hint": "Used in generated IMGT files"},
                      "confirmation_methods" : {"section" : "Method",
                                              "lbl_text" : "Confirmation Method",
                                              "hint": "Used in generated IMGT files"},
                      "type_of_primer" : {"section" : "Method",
                                          "lbl_text" : "Type of Primer",
                                          "hint": "Used in generated IMGT files"},
                      "sequencing_direction" : {"section" : "Method",
                                          "lbl_text" : "Sequencing Direction",
                                          "hint": "Used in generated IMGT files"},
                      "sequenced_in_isolation" : {"section" : "Method",
                                          "lbl_text" : "Sequenced in Isolation?",
                                          "hint": "Used in generated IMGT files"},
                      "no_of_reactions" : {"section" : "Method",
                                          "lbl_text" : "Number of reactions",
                                          "hint": "Used in generated IMGT files"},
                      "type_of_primer" : {"section" : "Method",
                                          "lbl_text" : "Type of Primer",
                                          "hint": "Used in generated IMGT files"},
                      
                      "fasta_extensions" : {"section" : "Pref",
                                          "lbl_text" : "Fasta File Extensions",
                                          "hint": "These extensions are recognized as fasta files. Must be separated by |, no whitespaces!"},
                      "pseudogenes" : {"section" : "Pref",
                                       "lbl_text" : "KIR Pseudogenes",
                                       "hint": "These KIR genes will be annotated as pseudogenes. Must be separated by |, no whitespaces!"},
                      "keep_recovery" : {"section" : "Pref",
                                          "lbl_text" : "Days to store recovery data",
                                          "hint": "This user account's logfiles and internal database copies older than this many days will be deleted during any session start."},
                      
                      "root_path" : {"section" : "Paths",
                                     "lbl_text" : "TypeLoader Data Location",
                                     "hint": "All TypeLoader data is saved here. This path is set during install and cannot be changed later!"},
                      "blast_path" : {"section" : "Paths",
                                     "lbl_text" : "BLAST File Location",
                                     "hint": "BLAST is located here."},
                      "raw_files_path" : {"section" : "Paths",
                                          "lbl_text" : "Default Raw Files Location",
                                          "hint": "When uploading new allele sequence files, TypeLoader will initially look here."},
                      "default_saving_dir" : {"section" : "Paths",
                                              "lbl_text" : "Default Saving Location",
                                              "hint": "When downloading files from TypeLoader, TypeLoader will initially offer to save them here."},
                      "timeout_ena": {"section": "Pref",
                                      "lbl_text": "ENA timeout after x seconds",
                                      "hint": "When submitting files to ENA, abort after this many seconds of no response from ENA."}
        }
    
    def init_UI(self):
        self.tabs_dic = {}
        self.add_tab("User Account", ["User"])
        self.add_tab("Company", ["Company"])
        self.add_tab("Method", ["Method"])
        self.add_tab("Preferences", ["Pref", "Paths"])
        
        # add special treatment:
        self.mydic["login"]["field"].setReadOnly(True)
        self.mydic["root_path"]["field"].setReadOnly(True)
        
        # add password change button
        self.pw_btn = QPushButton("Change Password", self)
        self.tabs_dic["User Account"].layout.addRow(self.pw_btn)
        self.pw_btn.clicked.connect(self.open_pw_editor)
        self.pw_btn.setWhatsThis("Opens a dialog that allows changing your password")

    def add_tab(self, text, sections):
        """creates a tab labelled <text> 
        containing all settings of sections <section> defined in self.prepare_settings() 
        """
        self.log.debug("Adding SettingsDialog tab {}...".format(text))
        mytab = QWidget()
        layout = QFormLayout()
        mytab.setLayout(layout)
        mytab.layout = layout
        
        combobox_fields = {"address_form" : ["Dr.", "Ms.", "Mrs.", "Mr.", "Ass. Prof.", "Prof.", "Med. Prof."],
                           "material_available" : ["No Material Available", "DNA", "Whole Blood Sample", 
                                                   "Peripheral Blood Lymphocytes", 
                                                   "Cell Line - B Lyphoblastoid Cell Line", "Cell Line - Burkitt's Line",
                                                   "Cell Line - Choriocarcinoma", "Cell Line - Endometrial Cell Line",
                                                   "Cell Line - Epithelial Cell Line", "Cell Line - Fibroblast Cell Line",
                                                   "Cell Line - Histiocytic macrophage", "Cell Line - Hodgkins Disease Cell Line",
                                                   "Cell Line - Human Hybridoma Partner", "Cell Line - Lyphocytes",
                                                   "Cell Line - Melanoma Cell Line", "Cell Line - Myeloid Cell Line",
                                                   "Cell Line - PBMC", "Cell Line - T Cell Line",
                                                   "Cell Line - Teratoma Cell Line", "Cell Line - unknown"],
                           "sequencing_direction" : ["OneSided", "Both"],
                           "sequenced_in_isolation" : ["yes", "no"],
                           "primary_sequencing" : ["NGS - Illumina Sequencing Technology", "NGS - Pacific Biosciences SMRT Technology",
                                                   "NGS - Oxford Nanopore Technology", "NGS - Ion Torrent Sequencing Technology",
                                                   "NGS - 454 Sequencing Technology",
                                                   "Direct sequencing of PCR product from DNA (SBT)",
                                                   "Direct sequencing of PCR product from RNA (SBT)",
                                                   "Cloning of PCR product & sequencing", "cDNA cloning and sequencing",
                                                   "cDNA amplification, cloning and sequencing", "Genomic Clones",
                                                   "Cosmids", "YAC Cloning and sequencing", "Protein Biochemistry"],
                           "secondary_sequencing" : ["NGS - Illumina Sequencing Technology", "NGS - Pacific Biosciences SMRT Technology",
                                                   "NGS - Oxford Nanopore Technology", "NGS - Ion Torrent Sequencing Technology",
                                                   "NGS - 454 Sequencing Technology",
                                                   "Direct sequencing of PCR product from DNA (SBT)",
                                                   "Direct sequencing of PCR product from RNA (SBT)",
                                                   "Cloning of PCR product & sequencing", "cDNA cloning and sequencing",
                                                   "cDNA amplification, cloning and sequencing", "Genomic Clones",
                                                   "Cosmids", "YAC Cloning and sequencing", "Protein Biochemistry",
                                                   "No Secondary methods used"],
                           "type_of_primer" : ["Locus specific", "Allele specific", "Generic Specific", 
                                               "Both allele and locus specific", "Both allele and generic specific", 
                                               "Both locus and generic specific", "None used"]}
        for section in sections:
            for (key, value) in self.cf.items(section):
                key = key.lower()
                if key in self.mydic:
                    if key in combobox_fields: # combo boxes
                        self.mydic[key]["type"] = "QComboBox"
                        self.mydic[key]["field"] = QComboBox(self)
                        self.mydic[key]["field"].addItem(value)
                        for v2 in combobox_fields[key]:
                            if v2 != value:
                                self.mydic[key]["field"].addItem(v2)
                        self.mydic[key]["field"].activated.connect(self.catch_unconfirmed_data)
                        self.mydic[key]["value"] = self.mydic[key]["field"].currentIndex()
                        self.mydic[key]["field"].setEditable(True)
                        self.mydic[key]["field"].editTextChanged.connect(self.catch_unconfirmed_data)
                    else: # line edits
                        self.mydic[key]["type"] = "QLineEdit"
                        self.mydic[key]["field"] = QLineEdit(value, self)
                        self.mydic[key]["field"].textChanged.connect(self.catch_unconfirmed_data)
                        self.mydic[key]["value"] = value
                    if "hint" in self.mydic[key]:
                        self.mydic[key]["field"].setWhatsThis(self.mydic[key]["hint"])
                    layout.addRow(QLabel(self.mydic[key]["lbl_text"] + ":"), self.mydic[key]["field"])
        
        self.addTab(mytab, text)
        self.tabs_dic[text] = mytab
    
    def catch_unconfirmed_data(self):
        """when any content is changed, emit self.content_changed
        """ 
        self.content_changed.emit()
        self.log.debug("SettingsTab emitted content_changed")
        
    def open_pw_editor(self):
        """opens the PasswordEditor
        """
        PasswordEditor(self.settings, self.log).exec_()


class UserSettingsDialog(QDialog):
    """a dialog to view and edit a user's settings
    """
    def __init__(self, settings, log, parent = None):
        super().__init__(parent)
        self.settings = settings
        self.log = log
        self.setWindowTitle("TypeLoader Settings")
        self.setWindowIcon(QIcon(general.favicon))
        self.resize(500,350)
        self.cf = ConfigParser()
        self.cf.read(self.settings["user_cf"])
        self.unconfirmed_changes = False
        self.init_UI()
        self.setModal(True)
        self.show()
        
    def init_UI(self):
        """establish and fill the UI
        """
        layout = QVBoxLayout(self)
        self.setLayout(layout)
        
        lbl = QLabel("Edit your TypeLoader Settings")
        lbl.setStyleSheet(general.label_style_main)
        layout.addWidget(lbl)
        
        self.tab_widget = SettingTab(self.log, self.cf, self)
        layout.addWidget(self.tab_widget)
        self.tab_widget.content_changed.connect(self.catch_unconfirmed_data)
        
        self.btns = ConfirmResetWidget([], self.log, parent= self)
        self.btns.confirm_btn.clicked.connect(self.save_changes)
        self.btns.reset_btn.clicked.connect(self.reset_changes)
        layout.addWidget(self.btns)
    
    @pyqtSlot()
    def catch_unconfirmed_data(self):
        """realize when any settings are changed
        """
        self.log.debug("SettingsDialog found unconfirmed changes")
        self.unconfirmed_changes = True
        self.btns.confirm_btn.highlight()
        self.btns.reset_btn.highlight()
    
    def on_data_confirm_reset(self):
        """realize when changes are saved or discarded 
        """
        self.log.debug("All changes confirmed or reset")
        self.unconfirmed_changes = False
        self.btns.confirm_btn.normalize()
        self.btns.reset_btn.normalize()
    
    def value_ok(self, field, value):
        """checks if format restrictions have been met 
        """
        mydic = {"cell_line_token" : "Cell line identifier",
                 "ipd_shortname" : "IPD Shortname"}
        if field in ["cell_line_token", "ipd_shortname"]:
            pattern = "[^a-zA-Z0-9\-]+"
            if re.search(pattern, value):
                QMessageBox.warning(self, "{} rejected".format(mydic[field]), 
                                    "Please use only letters, numbers or '-' in the {}!".format(mydic[field]))
                return False
            if len(value) > 10:
                QMessageBox.warning(self, "{} rejected".format(mydic[field]), 
                                    "Your {} is too long.\nPlease restrict yourself to max. 10 characters!".format(mydic[field]))
                return False

        if field == "timeout_ena":
            pattern = "[^0-9]+"
            if re.search(pattern, value):
                QMessageBox.warning(self,
                                    "ENA timeout value rejected",
                                    "The ENA timeout threshold must be a number of seconds!")

        return True
            
    @pyqtSlot()
    def save_changes(self):
        """completely regenerates config file if unconfirmed changes were found
        """
        if self.unconfirmed_changes:
            self.log.info("Saving edited settings...")
            mydic = self.tab_widget.mydic
            for setting in mydic:
                section = mydic[setting]["section"]
                field = mydic[setting]["field"]
                if mydic[setting]["type"] == "QComboBox":
                    value = field.currentText()
                    mydic[setting]["value"] = field.currentIndex()
                else:
                    value = field.text()
                    if not self.value_ok(setting, value):
                        self.log.warning("Value for {} is not ok! Rejecting...".format(setting))
                        return
                    mydic[setting]["value"] = value
                        
                self.cf.set(section, setting, value)
                self.settings[setting] = value
                
            with open(self.settings["user_cf"], "w") as g:
                self.cf.write(g)
            self.on_data_confirm_reset()
            self.log.info("\t=> All changes saved.")
        else:
            self.log.info("No unconfirmed changes found.")
                
    @pyqtSlot()
    def reset_changes(self):
        """resets all settings to the values of last saving
        """
        if self.unconfirmed_changes:
            self.log.info("Reverting all edits to settings...")
            mydic = self.tab_widget.mydic
            for setting in mydic:
                field = mydic[setting]["field"]
                old_value = mydic[setting]["value"]
                if mydic[setting]["type"] == "QComboBox":
                    field.setCurrentIndex(old_value)
                else:
                    field.setText(old_value)
            self.on_data_confirm_reset()
        else:
            self.log.info("No unconfirmed changes found.")
    
    def closeEvent(self, event):
        """make sure the dialog is not closed while there are unsaved changes
        """
        if self.unconfirmed_changes:
            QMessageBox.warning(self, "Unsaved changes", "You have unsaved changes. Please confirm or reset them before leaving!")
            event.ignore()
        else:
            event.accept()
            
            
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
    log.info("<Start {}>".format(os.path.basename(__file__)))
    settings_dic = GUI_login.get_settings("admin", log)
    app = QApplication(sys.argv)
    sys.excepthook = log_uncaught_exceptions
    
    ex = UserSettingsDialog(settings_dic, log)
#     ex = PasswordEditor(settings_dic, log)
    ex.show()#Maximized()
    result = app.exec_()
    
    log.info("<End>")
    sys.exit(result)


if __name__ == '__main__':
    main()

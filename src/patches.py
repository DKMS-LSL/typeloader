'''
Created on 27.11.2018

patches.py

implements retroactive changes to the database or config files

@author: Bianca Schoene
'''

import os, sys
from configparser import ConfigParser

from PyQt5.QtWidgets import (QApplication, QLabel, QMessageBox,
                             QDialog, QLineEdit, QFormLayout)
from PyQt5.Qt import pyqtSignal
from PyQt5.QtGui import QIcon

import general
from GUI_login import base_config_file, raw_config_file, company_config_file, user_config_file, get_settings
from GUI_forms import ProceedButton

#===========================================================
# global parameters:

patch_config_file = "config_patchme.ini"
    
#===========================================================
# classes:

class GetPatchInput(QDialog):
    """requests additional parameters from user for issue #57
    """
    sample_data = pyqtSignal(str, str)
    
    def __init__(self, root_path, log, parent = None):
        super().__init__()
        self.log = log
        self.root_path = root_path
        self.init_UI()
        self.setWindowIcon(QIcon(general.favicon))
        
    def init_UI(self):
        self.log.info("Requesting user input for necessary patches...")
        layout = QFormLayout()
        self.setLayout(layout)
        
        intro_lbl = QLabel("The new version of TypeLoader needs the following additional settings:")
        intro_lbl.setStyleSheet(general.label_style_2nd)
        layout.addRow(intro_lbl)
        
        intro_lbl2 = QLabel("(1) A short identifier for your company towards IPD. (IPD submission files will start with this.)\nAn acronym etc. is ideal:")
        intro_lbl2.setStyleSheet(general.label_style_italic)
        layout.addRow(intro_lbl2)
        self.ipd_short_fld = QLineEdit(self)
        layout.addRow(QLabel("IPD Shortname:"), self.ipd_short_fld)
        
        intro_lbl3 = QLabel("(2) The number of IPD submission files your company has already created with previous TypeLoader versions:")
        intro_lbl3.setStyleSheet(general.label_style_italic)
        layout.addRow(intro_lbl3)
        self.ipd_nr_fld = QLineEdit(self)
        self.ipd_nr_fld.setText("0")
        layout.addRow(QLabel("IPD Submission Nr:"), self.ipd_nr_fld)
        
        self.ok_btn = ProceedButton("Done", [self.ipd_short_fld, self.ipd_nr_fld], self.log)
        layout.addRow(self.ok_btn)
        self.ipd_short_fld.textChanged.connect(self.ok_btn.check_ready)
        self.ipd_nr_fld.textChanged.connect(self.ok_btn.check_ready)
        self.ok_btn.clicked.connect(self.on_clicked)
            
    def on_clicked(self):
        """when ok_btn is clicked, get content of fields and adjust config files
        """
        ipd_short = self.ipd_short_fld.text().strip()
        ipd_nr = self.ipd_nr_fld.text().strip()
        self.log.debug("\t=> IPD Shortname: {}".format(ipd_short))
        self.log.debug("\t=> IPD Submission Nr: {}".format(ipd_nr))
        self.log.info("Writing adjusted config files...")
        try:
            int(ipd_nr)
        except ValueError:
            QMessageBox.warning(self, "This is not a number!", "Please specify a number in the field 'IPD Submission Nr'!")
        
        self.log.debug("\tWriting patch config file...")
        with open(patch_config_file, "w") as g:
            g.write("[Company]\n")
            g.write("ipd_shortname = {}\n".format(ipd_short))
            g.write("ipd_submission_length = 7\n")
            
        self.log.debug("\tWriting submission counter file...")
        submission_counter_file = os.path.join(self.root_path, "_general", "counter_config.ini")
        with open(submission_counter_file, "w") as g:
            g.write("[Counter]\n")
            g.write("ipd_submissions = {}\n".format(ipd_nr))
        
        self.close()


#===========================================================
# functions:



def check_patching_necessary(log):
    """checks config files for missing values
    """
    log.debug("Checking if any config patches necessary...")
    patchme_dic = {company_config_file : {"Company" : ["ipd_shortname", "ipd_submission_length"]}
                   }
    needs_patching = False
    for config_file in patchme_dic:
        cf = ConfigParser()
        cf.read(config_file)
        for section in patchme_dic[config_file]:
            for option in patchme_dic[config_file][section]:
                if not cf.has_option(section, option):
                    msg = "Config files outdated: option '{}' in section [{}] of {}".format(option, section, config_file)
                    msg += " missing, please specify!"
                    log.warning(msg)
                    needs_patching = True
    if not needs_patching:
        log.debug("\t=> everything up to date")
    return needs_patching

def request_user_input(root_path, app, log):
    """calls a popup dialog to request additional user input for config files
    """
    dialog = GetPatchInput(root_path, log)
    dialog.show()
    app.exec_()

def get_users(root_path, log):
    """finds existing users
    """
    log.debug("Finding existing users...")
    users = []
    for user in os.listdir(root_path):
        if not user.startswith("_") and os.path.isdir(os.path.join(root_path, user)):
            if os.path.isfile(os.path.join(root_path, user, user_config_file)):
                users.append(user)
    log.debug("\t=> {} users found".format(len(users)))
    return users

def patch_config(root_path, users, log):
    """patches all existing config files if necessary
    """
    log.info("Patching config files if necessary...")
    if not os.path.isfile(patch_config_file):
        log.warning("No patch-config file found!")
        return
    
    cf_patch = ConfigParser()
    cf_patch.read(patch_config_file) # contains new fields to add
    
    config_file_dic = {"Company": company_config_file # format: {section_name: which basic config file must be updated} # it is assumed that all existing user.ini files must always be updated
                   } # only add sections once they need to be patched
    
    patch_for_users = [] # list of (section, key, value) tuples that need to be set in user config files 
    
    # patch basic config files as needed:
    for section in cf_patch.sections():
        my_cf_file = config_file_dic[section]
        cf_to_patch = ConfigParser()
        cf_to_patch.read(my_cf_file)
        needs_editing = False
        for (key, value) in cf_patch.items(section):
            try:
                myvalue = cf_to_patch.get(section, key)
            except:
                myvalue = None
            if value == myvalue: # if not already set
                log.debug("\t{} already up to date".format(key))
            else:
                log.debug("\tNew value in {}: [{}]: {} = {}".format(my_cf_file, section, key, value))
                cf_to_patch.set(section, key, value)
                patch_for_users.append((section, key, value))
                needs_editing = True
        if needs_editing:
            log.debug("\t=> Updating file {}...".format(my_cf_file))
            with open(my_cf_file, "w") as g:
                cf_to_patch.write(g)
        else:
            log.debug("\t=> No patching necessary")
            
    # patch existing user config files:
    if patch_for_users:
        log.debug("Patching individual user config files...")
        for user in users:
            log.debug("\t{}...".format(user))
            user_config = os.path.join(root_path, user, user_config_file)
            cf = ConfigParser()
            cf.read(user_config)
            for (section, key, value) in patch_for_users:
                cf.set(section, key, value)
            with open(user_config, "w") as g:
                cf.write(g)           
pass
#===========================================================
# main:

def execute_patches(root_path, log):
    """executes all patching
    """
    users = get_users(root_path, log)
    patch_config(root_path, users, log)
    

if __name__ == '__main__':
    from GUI_login import get_basic_cf
    log = general.start_log(level="DEBUG")
    log.info("<Start patches.py>")
    app = QApplication(sys.argv)
    cf = get_basic_cf()
    root_path = cf.get("Paths", "root_path")
    request_user_input(root_path, app, log)
    log.info("<End patches.py>")
    
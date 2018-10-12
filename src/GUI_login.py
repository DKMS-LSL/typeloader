#!/usr/bin/env python3
# -*- coding: cp1252 -*-
'''
Created on 20.06.2018

GUI_login.py

contains classes and functions for login & user handling functionality

@author: Bianca Schoene
'''

# import modules:

import os, sys, shutil, logging, platform, urllib
from configparser import ConfigParser
from PyQt5.QtWidgets import (QApplication, QDialog, QFormLayout,
                             QMessageBox, QLabel, QPushButton,  
                             QLineEdit, QStyleFactory)
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtGui import QIcon

import general, db_internal
from authuser import user
from GUI_forms import ProceedButton

#===========================================================
# parameters:
base_config_file = "config_base.ini"
raw_config_file = "config_raw.ini"
company_config_file = "config_company.ini"
user_config_file = "config.ini"

from __init__ import __version__
#===========================================================
# classes:

class NewUserForm(QDialog):
    """a dialog to add a new user
    """
    def __init__(self, log, parent = None):
        super().__init__(parent)
        self.log = log
        self.user_db = parent.user_db
        self.setWindowTitle("New User")
        self.setWindowIcon(QIcon(general.favicon))
        self.init_UI()
        self.show()
        
    def init_UI(self):
        layout = QFormLayout(self)
        lbl = QLabel("Create new user:")
        lbl.setStyleSheet(general.label_style_main)
        layout.addRow(lbl)
        
        self.user_field = QLineEdit(self)
        layout.addRow(QLabel("User name:"), self.user_field)
        
        self.pwd_field = QLineEdit(self)
        self.pwd_field.setEchoMode(QLineEdit.Password)
        layout.addRow(QLabel("Password:"), self.pwd_field)
        
        self.add_field = QLineEdit(self)
        self.add_field.setPlaceholderText("Dr.")
        layout.addRow(QLabel("Form of address:"), self.add_field)
        
        self.name_field = QLineEdit(self)
        layout.addRow(QLabel("Full Name:"), self.name_field)
        
        self.short_field = QLineEdit(self)
        self.short_field.setPlaceholderText("(optional)")
        layout.addRow(QLabel("Initials:"), self.short_field)
        
        self.email_field = QLineEdit(self)
        self.email_field.setPlaceholderText("(optional)")
        layout.addRow(QLabel("Email:"), self.email_field)
        
        fields = [self.user_field, self.name_field, self.pwd_field]
        ok_btn = ProceedButton("Create user!", items = fields, log = self.log, parent = self)
        for item in fields:
            item.textChanged.connect(ok_btn.check_ready)
        ok_btn.proceed.connect(self.make_new_user)
        layout.addRow(ok_btn)
        
    @pyqtSlot()
    def make_new_user(self, _ = None):
        """adds user to user_dic
        """
        try:
            self.log.info("Creating new user...")
            self.login = self.user_field.text().strip()
            self.pwd = self.pwd_field.text().strip()
            self.name = self.name_field.text().strip()
            self.short = self.short_field.text().strip()
            self.address = self.add_field.text().strip()
            if not self.address:
                self.address = "Dr."
            self.email = self.email_field.text().strip()
            
            if not self.short: # make initials
                for word in self.name.split():
                    self.short += word[0].upper()
            
            try:
                self.user_db.add_user(self.login, self.pwd)
                self.accept()
            except Exception:
                QMessageBox.warning(self, "Username exists", "This user exists already!")

        except Exception as E:
            self.log.error(E)
            self.log.exception(E)
            QMessageBox.warning(self, "Cannot create user", 
                                "An error occurred while creating user '{}':\n\n{}".format(repr(E)))
            return False
        

class LoginForm(QDialog):
    """A simple user login dialog
    """
    def __init__(self, log, parent=None):
        super().__init__(parent)
        self.log = log
        self.log.debug("Starting login...")
        
        self.setWindowTitle("TypeLoader Login")
        self.setWindowIcon(QIcon(general.favicon))

        # get root path from base config:
        cf = ConfigParser()
        log.debug("Reading basic config from {}...".format(os.path.abspath(base_config_file)))
        cf.read(base_config_file)
        self.root_path = cf.get("Paths", "root_path")
        log.debug("root path: {}".format(self.root_path))
        
        pickle_file = os.path.join(self.root_path, "_general", "user.pickle")
        log.debug("pickle_file: {}".format(pickle_file))
        self.user_db = user.User(os.path.join(pickle_file))
        
        self.init_UI()
        self.check_latest_version(self.log)
        
    def init_UI(self):
        layout = QFormLayout(self)
        
        lbl = QLabel("Welcome to TypeLoader!")
        lbl.setStyleSheet(general.label_style_main)
        layout.addRow(lbl)
        
        self.user_field = QLineEdit(self)
        layout.addRow(QLabel("User name:"), self.user_field)
        
        self.pwd_field = QLineEdit(self)
        self.pwd_field.setEchoMode(QLineEdit.Password)
        layout.addRow(QLabel("Password:"), self.pwd_field)
        
        self.login_btn = QPushButton('Login', self)
        layout.addRow(self.login_btn)
        self.login_btn.clicked.connect(self.handle_login)
        
        self.remove_lock_btn = QPushButton("Remove user lock", self)
        self.remove_lock_btn.setWhatsThis("If your login is blocked because the GUI crashed during the last run, you can remove the lock here.")
        layout.addRow(self.remove_lock_btn)
        self.remove_lock_btn.clicked.connect(self.remove_lock)
        self.remove_lock_btn.setEnabled(False)
        self.new_user_btn = QPushButton("Create new user", self)
        self.new_user_btn.clicked.connect(self.handle_new_user)
        layout.addRow(self.new_user_btn)

    @pyqtSlot()
    def handle_login(self):
        """checks whether user-pwd combo is ok;
        if yes, emits user_name and accepts login
        """
        try:
            login_ok = self.check_login()
            if login_ok:
                locked = self.check_lock()
                if not locked:
                    self.accept()
                    
        except Exception as E:
            self.log.exception(E)
            QMessageBox.warning(self, "login error",
                        "An error occured during login: \n\n{}".format(repr(E)))
    
    def check_login(self):
        """checks whether login data is ok
        """
        ok = False
        self.login= self.user_field.text().strip()
        self.pwd = self.pwd_field.text().strip()
        
        if self.user_db.authenticate_user(self.login, self.pwd):
            ok = True
        
        if not ok:
            self.handle_bad_login()
        
        return ok
            
    def handle_bad_login(self):
        self.log.info("Bad username or password")
        msgBox = QMessageBox()
        msgBox.setWindowIcon(QIcon(general.favicon))
        msgBox.setWindowTitle('Login Error')
        msgBox.setIcon(QMessageBox.Warning)
        msgBox.setText("Bad username or password")
        msgBox.addButton(QPushButton('Ok'), QMessageBox.YesRole)
        msgBox.addButton(QPushButton('Reset Password'), QMessageBox.ActionRole)
        ret = msgBox.exec_()
    
        if ret == 1: # if reset password
            self.log.info("Password reset requested. Are you sure?")
            reply = QMessageBox.question(self, "Password Reset", 
                                         "Are you sure you want to reset your password to nothing?",
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
    
            if reply == QMessageBox.Yes:
                if self.login in self.user_db.all_credentials:
                    self.log.info("Resetting password for user {}...".format(self.login))
                    
                    self.user_db.modify_user(self.login, "")
                    QMessageBox.information(self, "Password was reset", "Your password was reset to empty. You can now login without password.\nAfter logging in, please use the settings dialog to change your password again!")
                else:
                    QMessageBox.warning(self, "Unknown user", "User name {} does not exist. Please use the 'Create new user' button to create it!".format(self.login))
            else:
                self.log.info("Keeping password unchanged")
                
    @pyqtSlot()
    def handle_new_user(self):
        """starts NewUserForm dialog to catch data for a new user
        """
        try:
            dialog = NewUserForm(self.log, self)
            result = dialog.exec_()
            if result == QDialog.Accepted:
                self.login = dialog.login
                self.pwd = dialog.pwd
                self.name = dialog.name
                self.short = dialog.short
                self.address = dialog.address
                self.email = dialog.email
            
                if self.login == "admin":
                    QMessageBox.warning(self, "User creation error", 
                            "Username 'admin' is restricted. Please use something else!")
                    return
                
                success = create_user_space(self.root_path, self.login, self.name, 
                                            self.short, self.email, self.address, self.log)
                if not success:
                    QMessageBox.warning(self, "User creation error", 
                            "Cannot create user path because it already exists!")
                    return
            
                self.log.debug("=> created user {}".format(self.login))
                self.accept()
            else:
                QMessageBox.warning(
                    self, 'Error', 'Could not create new user')
                
        except Exception as E:
            self.log.error(E)
            self.log.exception(E)
            QMessageBox.warning(
                self, 'New user error', 'An error occurred while trying to create a new user:\n\n{}'.format(repr(E)))
    
    @pyqtSlot()
    def check_lock(self):
        """checks whether this login is currently in use;
        if not, creates lock
        """
        self.log.debug("Checking lock...")
        locked = False
        if self.login == "staging": # staging user has different paths depending on the os used
            cf, _, myos = get_raw_settings("staging", self.log)
            if myos == "Windows":
                self.root_path = cf.get("Paths", "staging_path_windows")
            else:
                self.root_path = cf.get("Paths", "staging_path_linux")
        self.user_dir = os.path.join(self.root_path, self.login)
        self.lockfile = os.path.join(self.user_dir, ".locked")
        if os.path.isfile(self.lockfile):
            msg = "This login is currently used by someone else!"
            self.log.warning(msg)
            self.log.debug(self.lockfile)
            QMessageBox.warning(self, "Locked", msg)
            locked = True
            self.remove_lock_btn.setEnabled(True)
        else: 
            locked = False
            self.log.debug("=> Login is available, proceeding...")
            #create lockfile
            try:
                with open(self.lockfile, "w") as _:
                    os.utime(self.lockfile)
            except Exception as E:
                self.log.warning("Could not create lockfile under {}: {}".format(self.lockfile, repr(E)))
    
        return locked
    
    @pyqtSlot()
    def remove_lock(self):
        """removes the lockfile if it remained after a GUI crash
        """
        self.log.info("Requesting lock removal...")
        login_ok = self.check_login()
        if login_ok:
            if os.path.isfile(self.lockfile):
                reply = QMessageBox.question(self, 'Remove lock?',
                "Are you sure you want to remove user '{}''s lockfile? \n\n(Only use this if you're sure the lock is there because TypeLoader crashed during your last session!)".format(self.login), QMessageBox.Yes | 
                                                                QMessageBox.No, QMessageBox.Yes)
                if reply == QMessageBox.Yes:
                    self.log.info("Removing lock from user '{}'...".format(self.login))
                    os.remove(self.lockfile)
                    self.accept()
                else:
                    self.log.info("Not removing lock.")


    def check_latest_version(self, log):
        """checks whether current version is up to date;
        if not, opens an infobox
        """
        github_repo = r"https://github.com/DKMS-LSL/typeloader"
        github_init = r"https://raw.githubusercontent.com/DKMS-LSL/typeloader/master/src/__init__.py"
        newer_version, error, msg = check_for_newer_version(github_init, github_repo, log)
        if error:
            if newer_version:
                QMessageBox.information(self, error, msg)
            else:
                QMessageBox.warning(self, error, msg)
pass

#===========================================================
# functions:

def make_new_settings(root_path, user, user_name, short_name, email, address,
                      log):
    """creates config file for a new user
    """
    log.info("Establishing user settings for new user {}...".format(user))
    user_ini = os.path.join(root_path, user, user_config_file)
    
    # concatenate raw user config with company config:
    with open(user_ini, "w") as g:
        with open(raw_config_file, "r") as f:
            for line in f:
                g.write(line)
        
        if user.lower().startswith("test") or user.lower() == "admin":
            g.write("use_ena_server: TEST\n")
            g.write("modus: testing\n\n")
        else:
            g.write("use_ena_server: PROD\n")
            g.write("modus: productive\n\n")
            
        with open(company_config_file, "r") as f:
            for line in f:
                g.write(line)
                
        g.write("[Paths]\n")
        g.write("raw_files_path: {}\n".format("C:\\"))
        g.write("default_saving_dir: {}\n".format("C:\\"))
        cf = get_basic_cf(log)
        g.write("root_path: {}\n".format(cf.get("Paths", "root_path")))
        g.write("blast_path: {}\n".format(cf.get("Paths", "blast_path")))
        
        # add user paths:
        user_dir = os.path.join(root_path, user)
        log.debug("Preparing user dir under {}".format(user_dir))
        g.write("login_dir: {}\n".format(user_dir))
        projects_dir = os.path.join(user_dir, "projects")
        g.write("projects_dir: {}\n".format(projects_dir))
        g.write("temp_dir: {}\n".format(os.path.join(user_dir, "temp")))
        g.write("recovery_dir: {}\n".format(os.path.join(user_dir, "recovery")))
        g.write("db_file: {}\n".format(os.path.join(user_dir, "data.db")))
        g.write("dat_path: {}\n".format(root_path))
        
        # add user section:
        g.write("\n[User]\n")
        g.write("login: {}\n".format(user))
        g.write("user_name: {}\n".format(user_name))
        g.write("short_name: {}\n".format(short_name))
        g.write("email: {}\n".format(email))
        g.write("address_form: {}\n".format(address))
    
    log.info("\t=> Done!")
    return user_ini


def get_basic_cf(log=None):
    """extracts data from base_config.ini
    """
    if log:
        log.info("Loading base config from {}...".format(os.path.abspath(base_config_file)))
    cf = ConfigParser()
    cf.read(base_config_file)
    return cf


def get_raw_settings(user, log, cf = None):
    """reads settings from user's config_file
    """
    if not cf:
        cf = get_basic_cf(log)
    myos = platform.system()
    if user == "staging":
        if myos == "Windows":
            root_path = cf.get("Paths", "staging_path_windows")
            ini_file = "config_win.ini"
        else:
            root_path = cf.get("Paths", "staging_path_linux")
            ini_file = "config_linux.ini"
    else:
        root_path = cf.get("Paths", "root_path")
        ini_file = user_config_file
    user_cf_file = os.path.join(root_path, user, ini_file)
    cf.read(user_cf_file)
    return cf, user_cf_file, myos
    
    
def get_settings(user, log, cf = None):
    """translates user's read config file into settings_dic 
    """
    log.info("Loading user settings...")
    cf, user_cf_file, myos = get_raw_settings(user, log, cf)
    
    if not os.path.isfile(user_cf_file):
        log.error("\tUser settings file {} not found!".format(user_cf_file))
        return None
    
    settings_dic = {"user_cf" : user_cf_file, # user's config file
                    "os" : myos # current operating system
                    } 
    for section in cf.sections():
        for (key, value) in cf.items(section):
            settings_dic[key] = value   
    if settings_dic["modus"] in ["testing", "debugging"]:
        settings_dic["embl_submission"] = settings_dic["embl_submission_test"]
    log.info("\t=>Success")
    return settings_dic
    

def create_user_space(root_path, user, user_name, short_name, email, address, log):
    """creates folders and empty db for new user
    """
    user_dir = os.path.join(root_path, user)
    log.debug("Creating user dir under {}".format(user_dir))
    os.makedirs(user_dir, exist_ok = True)
    make_new_settings(root_path, user, user_name, short_name, email, address, log)
    settings_dic = get_settings(user, log)
    
    log.info("Creating new user space...")
    try:
        os.makedirs(settings_dic["projects_dir"])
        os.makedirs(settings_dic["temp_dir"])
        os.makedirs(settings_dic["recovery_dir"])
        lockfile = os.path.join(settings_dic["login_dir"], ".locked")
        with open(lockfile, "w") as _:
            os.utime(lockfile)
            
        log.info("Creating empty database...")
        db_internal.make_clean_db(settings_dic["db_file"], log)
        return True
    except FileExistsError:
        return False


def start_logfile(log, settings_dic, curr_time):
    """creates a logfile and starts writing to it
    """
    logfile = os.path.join(settings_dic["login_dir"], settings_dic["recovery_dirname"], "{}.log".format(curr_time))
    file_handler = logging.FileHandler(logfile)
    formatter = logging.Formatter('%(levelname)s [%(asctime)s] - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)
    log.addHandler(file_handler)
    log.info("<Starting logfile>")
    log.info("Typeloader V{} started by user {}".format(__version__, settings_dic["login"]))


def dump_db(curr_time, settings_dic, log):
    """saves a copy of data.db as _data.db before starting the app
    """
    log.debug("Saving a copy of the SQLite database...")
    db_file = os.path.join(settings_dic["login_dir"], settings_dic["db_filename"])
    db_file_temp = os.path.join(settings_dic["recovery_dir"], "{}_data.db".format(curr_time))
    shutil.copy(db_file, db_file_temp)
    

def startup(user, curr_time, log):
    """performs startup actions 
    (between 'login accepted' and 'main window start')
    """ 
    settings_dic = get_settings(user, log)
    start_logfile(log, settings_dic, curr_time)
    dump_db(curr_time, settings_dic, log)
    
    return settings_dic


def get_latest_version(myurl, repo, log):
    """retrieves latest version from __init__.py in the official GitHub repo
    """
    log.debug("\tRetrieving latest TypeLoader version from {}...".format(myurl))
    version = None
    msg = None
    try:
        with urllib.request.urlopen(myurl, timeout=5) as url:
            html = url.read()
            content = html.decode("UTF-8", "ignore")
        for line in content.split("\n"):
            if line.startswith("__version__"):
                if '"' in line:
                    version = line.split('"')[1]
                elif "'" in line:
                    version = line.split("'")[1]
                else:
                    log.debug("\t\t!Did not find a quote delimiter in the version line!")
    except Exception as E:
        log.exception(E)   
             
    if version:
        log.debug("\t\tlatest version: {}".format(version))
        return version, msg
    else:
        log.debug("\t\t!Could not find version on the given page!")
        msg = "Could not get current version from {}.".format(repo)
        msg += "\nPlease check if there is a new version available!"
        return version, msg


def check_for_newer_version(myurl, repo, log):
    """compares latest version with current version 
     and returns 'please update' message if necessary
    """
    log.info("Checking for never version...")
    newer_version = False
    error = None
    latest_version, msg = get_latest_version(myurl, repo, log)
    if not latest_version: # could not get current version from github
        error = "NewVersion Error"
        return newer_version, error, msg
    else:
        if latest_version > __version__:
            newer_version = True
            error = "Newer version available!"
            msg = "TypeLoader version {} is available!\n\n".format(latest_version)
            msg += "You are currently using version {}.\n".format(__version__)
            msg += "Please get the new version from {}!".format(repo)
            return newer_version, error, msg
        else:
            log.info("\t=> You are currently using the newest version of TypeLoader. :)")
            return newer_version, error, False
    
        
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


def config_files_missing():
    """checks whether the config files exist
    """
    for myfile in [base_config_file, company_config_file]: 
        if not os.path.isfile(myfile):
            print("File {} does not exist! Please create it before trying again!\nAborting...".format(myfile))
            return True
    return False
    
    

# def generate_inis(log):
#     from settings_ import user_dic
#     for user in user_dic:
#         root_path = r"\\nasdd12\daten\data\Typeloader"
#         user_name = user_dic[user]["user_name"]
#         short_name = user_dic[user]["short_name"]
#         email = user_dic[user]["email"]
#         address = user_dic[user]["address"]
#          
#         make_new_settings(root_path, user, user_name, short_name, email, address,
#                           log)


def check_root_path(root_path):
    """checks whether root_path and '_general' subdir was already created 
    (should happen during setup, but sometimes doesn't due to missing privileges),
    if not, creates them
    """  
    import errno
    general_dir = os.path.join(root_path, "_general")
    if os.path.isdir(general_dir):
        return
    else:
        try:
            os.makedirs(general_dir)
        except OSError as e:
            if e.errno != errno.EEXIST: # if dir creation fails for any reason except "dir exists already" 
                raise

pass
#===========================================================
# main:
    
if __name__ == '__main__':
    from typeloader_GUI import create_connection, close_connection, MainGUI, remove_lock
    log = general.start_log(level="DEBUG")
    log.info("<Start {} V{}>".format(os.path.basename(__file__), __version__))
    sys.excepthook = log_uncaught_exceptions
    
#     generate_inis(log)
    
    app = QApplication(sys.argv)
    app.setStyle(QStyleFactory.create("Fusion"))
      
    login = LoginForm(log)
    result = None
    if login.exec_() == QDialog.Accepted:
        user = login.login
        settings_dic = get_settings(user, log)
        db_file = settings_dic["db_file"]
           
        mydb = create_connection(log, db_file) 
   
        ex = MainGUI(mydb, log, settings_dic)
        ex.showMaximized()
        result = app.exec_()
               
        close_connection(log, mydb)
        remove_lock(settings_dic, log)
      
    log.info("<End>")
    sys.exit(result)

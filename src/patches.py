'''
Created on 27.11.2018

patches.py

implements retroactive changes to the database or config files

@author: Bianca Schoene
'''

import os, sys
import re
from configparser import ConfigParser

from PyQt5.QtWidgets import (QApplication, QLabel, QMessageBox,
                             QDialog, QLineEdit, QFormLayout)
from PyQt5.Qt import pyqtSignal
from PyQt5.QtGui import QIcon

import general, db_internal
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
        
        intro_lbl3 = QLabel("(3) A short identifier for your company to use for cell line naming. An acronym etc. is ideal:")
        intro_lbl3.setStyleSheet(general.label_style_italic)
        layout.addRow(intro_lbl3)
        self.token_fld = QLineEdit(self)
        self.token_fld.setPlaceholderText("Can be identical to IPD shortname; max. 10 characters, only alphanumeric or '-'.")
        layout.addRow(QLabel("Cell line identifier:"), self.token_fld)
        
        self.ok_btn = ProceedButton("Done", [self.ipd_short_fld, self.ipd_nr_fld, self.token_fld], self.log)
        layout.addRow(self.ok_btn)
        self.ipd_short_fld.textChanged.connect(self.ok_btn.check_ready)
        self.ipd_nr_fld.textChanged.connect(self.ok_btn.check_ready)
        self.token_fld.textChanged.connect(self.ok_btn.check_ready)
        self.ok_btn.clicked.connect(self.on_clicked)
            
    def on_clicked(self):
        """when ok_btn is clicked, get content of fields and adjust config files
        """
        ipd_short = self.ipd_short_fld.text().strip()
        ipd_nr = self.ipd_nr_fld.text().strip()
        token = self.token_fld.text().strip()
        self.log.debug("\t=> IPD Shortname: {}".format(ipd_short))
        self.log.debug("\t=> IPD Submission Nr: {}".format(ipd_nr))
        self.log.debug("\t=> Cell line identifier: {}".format(token))
        self.log.info("Writing adjusted config files...")
        
        #sanity checks:
        try:
            int(ipd_nr)
        except ValueError:
            QMessageBox.warning(self, "This is not a number!", "Please specify a number in the field 'IPD Submission Nr'!")
            self.ok_btn.setChecked(False)
            return
        pattern = "[^a-zA-Z0-9\-]+"
        if re.search(pattern, token):
            QMessageBox.warning(self, "Identifier rejected", "Please use only letters, numbers or '-' in the Cell line identifier!")
            self.ok_btn.setChecked(False)
            return
        if len(token) > 10:
            self.ok_btn.setChecked(False)
            QMessageBox.warning(self, "Identifier rejected", "Your cell line identifier is too long.\nPlease restrict yourself to max. 10 characters!")
            return
        
        # write config files:
        self.log.debug("\tWriting patch config file...")
        with open(patch_config_file, "w") as g:
            g.write("[Company]\n")
            g.write("ipd_shortname = {}\n".format(ipd_short))
            g.write("ipd_submission_length = 7\n")
            g.write("cell_line_token = {}\n".format(token))
            g.write("last_tl_version = 2.1.0\n")
            
        self.log.debug("\tWriting submission counter file...")
        submission_counter_file = os.path.join(self.root_path, "_general", "counter_config.ini")
        with open(submission_counter_file, "w") as g:
            g.write("[Counter]\n")
            g.write("ipd_submissions = {}\n".format(ipd_nr))
        
        self.close()


#===========================================================
# functions for config patches:

def check_patching_necessary(log):
    """checks config files for missing values
    """
    log.debug("Checking if any config patches necessary...")
    patchme_dic = {company_config_file : {"Company" : ["ipd_shortname", "ipd_submission_length", 
                                                       "last_tl_version", "cell_line_token"]}
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
# functions for database patches:

def replace_cell_line_in_FILES(conn, cursor, log):
    """table FILES: replaces column cell_line with local_name
    """
    log.info("Replacing column cell_line of table FILES with local_name...")
    q0_drop_new_table = "DROP TABLE FILES_NEW" #if table remains from error during last attempt
    try:
        cursor.execute(q0_drop_new_table)
    except: # if it's not there that's fine (it should not be there!)
        pass
    
    q1_new_table = """CREATE TABLE FILES_NEW 
                (SAMPLE_ID_INT TEXT , ALLELE_NR INT , LOCAL_NAME TEXT PRIMARY KEY, PROJECT TEXT , 
                RAW_FILE_TYPE TEXT , RAW_FILE TEXT , FASTA TEXT , BLAST_XML TEXT , 
                ENA_FILE TEXT , ENA_RESPONSE_FILE TEXT , IPD_SUBMISSION_FILE TEXT )"""
    cursor.execute(q1_new_table)
    q2_copy_data = """INSERT INTO FILES_NEW 
                (SAMPLE_ID_INT, ALLELE_NR,
                PROJECT, RAW_FILE_TYPE, RAW_FILE, FASTA, BLAST_XML, 
                ENA_FILE, ENA_RESPONSE_FILE, IPD_SUBMISSION_FILE)
            SELECT SAMPLE_ID_INT, ALLELE_NR, 
                PROJECT, RAW_FILE_TYPE, RAW_FILE, FASTA, BLAST_XML, 
                ENA_FILE, ENA_RESPONSE_FILE, IPD_SUBMISSION_FILE 
            FROM FILES"""
    cursor.execute(q2_copy_data)
    q3_drop_old_table = "DROP TABLE FILES"
    cursor.execute(q3_drop_old_table)
    q4_rename_new_table = "ALTER TABLE FILES_NEW RENAME TO FILES"
    cursor.execute(q4_rename_new_table)
    conn.commit()
    log.info("\t=> Done")


def add_missing_local_names_to_FILES(conn, cursor, log):
    """table FILES: adds missing local names
    """
    log.info("Adding local_names to table FILES...")
    log.info("\tGetting local_names from table ALLELES...")
    query = "select local_name, sample_id_int, allele_nr from ALLELES"
    items = db_internal.query_database(query, None, log, cursor)
    
    log.info("\tWriting local_names into table FILES...")
    update_query = "update or ignore FILES set local_name = :1 where sample_id_int = :2 and allele_nr = :3"
    cursor.executemany(update_query, items)
    conn.commit()
    log.info("\t=> Done")  


def add_cell_line_to_SAMPLES(settings, conn, cursor, log):
    """table SAMPLES: adds missing column cell_line
    """
    log.info("Adding column cell_line to table SAMPLES...")
    q1_add_column = "alter table SAMPLES add column CELL_LINE"
    cursor.execute(q1_add_column)
    
    log.debug("\tGetting existing samples...")
    q2_get_samples = "select sample_id_int, sample_id_ext from SAMPLES"
    items = db_internal.query_database(q2_get_samples, None, log, cursor)
    
    items = [('{}_{}'.format(settings["cell_line_token"], item[0]), item[0], item[1]) for item in items]
    log.info("\tWriting local_names into table FILES...")
    update_query = "update SAMPLES set cell_line = :1 where sample_id_int = :2 and sample_id_ext = :3"
    cursor.executemany(update_query, items)
    conn.commit()
    log.info("\t=> Done") 
    
    
def change_pk_of_ALLELES(conn, cursor, log):
    """table ALLELES: moves primary key to column local_name
    """
    log.info("Changing primary key of table ALLELES to column local_name and renames column cell_line...")
    q0_drop_new_table = "DROP TABLE ALLELES_NEW" #if table remains from error during last attempt
    try:
        cursor.execute(q0_drop_new_table)
    except: # if it's not there that's fine (it should not be there!)
        pass
    
    q1_new_table = """CREATE TABLE ALLELES_NEW 
                (SAMPLE_ID_INT TEXT , ALLELE_NR INT , PROJECT_NAME TEXT , PROJECT_NR INT , CELL_LINE_OLD TEXT,
                LOCAL_NAME TEXT PRIMARY KEY, GENE TEXT , GOAL TEXT , ALLELE_STATUS TEXT , 
                ORIG_ALLELE1 TEXT , 
                ORIG_ALLELE2 TEXT , ORIG_GENOTYPING_SOFTWARE TEXT , ORIG_SOFTWARE_VERSION TEXT , 
                ORIG_GENOTYPING_DATE TEXT , LAB_STATUS TEXT , PANEL TEXT , POSITION TEXT , SHORT_READ_DATA TEXT , 
                SHORT_READ_PHASING TEXT , SHORT_READ_TECHNOLOGY TEXT , LONG_READ_DATA TEXT , 
                LONG_READ_PHASING TEXT , LONG_READ_TECHNOLOGY TEXT , KOMMENTAR TEXT , TARGET_ALLELE TEXT , 
                PARTNER_ALLELE TEXT , MISMATCH_POSITION TEXT , NULL_ALLELE TEXT , 
                NEW_GENOTYPING_SOFTWARE TEXT , NEW_SOFTWARE_VERSION TEXT , NEW_GENOTYPING_DATE TEXT , 
                REFERENCE_DATABASE TEXT , DATABASE_VERSION TEXT , INTERNAL_NAME TEXT , OFFICIAL_NAME TEXT , 
                NEW_CONFIRMED TEXT , ENA_SUBMISSION_ID TEXT , ENA_ACCEPTION_DATE TEXT , ENA_ACCESSION_NR TEXT , 
                IPD_SUBMISSION_ID TEXT , IPD_SUBMISSION_NR TEXT , HWS_SUBMISSION_NR TEXT , IPD_ACCEPTION_DATE TEXT , 
                IPD_RELEASE TEXT, UPLOAD_DATE TEXT, DETECTION_DATE TEXT)
                """
    cursor.execute(q1_new_table)
    q2_copy_data = """
        INSERT INTO ALLELES_NEW 
            (SAMPLE_ID_INT, ALLELE_NR, PROJECT_NAME, PROJECT_NR, CELL_LINE_OLD,
            LOCAL_NAME, GENE, GOAL, ALLELE_STATUS,
            ORIG_ALLELE1, ORIG_ALLELE2, ORIG_GENOTYPING_SOFTWARE, ORIG_SOFTWARE_VERSION, 
            ORIG_GENOTYPING_DATE, LAB_STATUS, PANEL, POSITION, SHORT_READ_DATA, 
            SHORT_READ_PHASING, SHORT_READ_TECHNOLOGY, LONG_READ_DATA, 
            LONG_READ_PHASING, LONG_READ_TECHNOLOGY, KOMMENTAR, TARGET_ALLELE, 
            PARTNER_ALLELE, MISMATCH_POSITION, NULL_ALLELE, 
            NEW_GENOTYPING_SOFTWARE, NEW_SOFTWARE_VERSION, NEW_GENOTYPING_DATE, 
            REFERENCE_DATABASE, DATABASE_VERSION, INTERNAL_NAME, OFFICIAL_NAME, 
            NEW_CONFIRMED, ENA_SUBMISSION_ID, ENA_ACCEPTION_DATE, ENA_ACCESSION_NR, 
            IPD_SUBMISSION_ID, IPD_SUBMISSION_NR, HWS_SUBMISSION_NR, IPD_ACCEPTION_DATE, 
            IPD_RELEASE, UPLOAD_DATE, DETECTION_DATE)
        SELECT 
            SAMPLE_ID_INT, ALLELE_NR, PROJECT_NAME, PROJECT_NR, CELL_LINE,
            LOCAL_NAME, GENE, GOAL, ALLELE_STATUS,
            ORIG_ALLELE1, ORIG_ALLELE2, ORIG_GENOTYPING_SOFTWARE, ORIG_SOFTWARE_VERSION, 
            ORIG_GENOTYPING_DATE, LAB_STATUS, PANEL, POSITION, SHORT_READ_DATA, 
            SHORT_READ_PHASING, SHORT_READ_TECHNOLOGY, LONG_READ_DATA, 
            LONG_READ_PHASING, LONG_READ_TECHNOLOGY, KOMMENTAR, TARGET_ALLELE, 
            PARTNER_ALLELE, MISMATCH_POSITION, NULL_ALLELE, 
            NEW_GENOTYPING_SOFTWARE, NEW_SOFTWARE_VERSION, NEW_GENOTYPING_DATE, 
            REFERENCE_DATABASE, DATABASE_VERSION, INTERNAL_NAME, OFFICIAL_NAME, 
            NEW_CONFIRMED, ENA_SUBMISSION_ID, ENA_ACCEPTION_DATE, ENA_ACCESSION_NR, 
            IPD_SUBMISSION_ID, IPD_SUBMISSION_NR, HWS_SUBMISSION_NR, IPD_ACCEPTION_DATE, 
            IPD_RELEASE, UPLOAD_DATE, DETECTION_DATE
        FROM ALLELES"""
    cursor.execute(q2_copy_data)
    q3_drop_old_table = "DROP TABLE ALLELES"
    cursor.execute(q3_drop_old_table)
    q4_rename_new_table = "ALTER TABLE ALLELES_NEW RENAME TO ALLELES"
    cursor.execute(q4_rename_new_table)
    conn.commit()
    log.info("\t=> Done")
    

def update_last_tl_version(settings, version, log):
    """updates the last_tl_version setting of this user with the current software version
    after all patches are done
    """
    log.info("Updating user config with current version {}...".format(version))
    user_config = settings["user_cf"]
    cf = ConfigParser()
    cf.read(user_config)
    cf.set("Company", "last_tl_version", version)
    with open(user_config, "w") as g:
        cf.write(g)
    log.info("\t=> Done")
    

def patch_database(settings, version, log):
    """patches the SQLite database of the current user
    """
    log.info("Patching database if necessary...")
    
    last_patched_tl_version = settings["last_tl_version"]
    if last_patched_tl_version > "2.2":
        log.info("\t=> everything up to date")
        return
    log.info("\t=> patching needed!")
    
    try:
        conn, cursor = db_internal.open_connection(settings["db_file"], log)
    
        add_cell_line_to_SAMPLES(settings, conn, cursor, log)
        change_pk_of_ALLELES(conn, cursor, log)
        replace_cell_line_in_FILES(conn, cursor, log)
        add_missing_local_names_to_FILES(conn, cursor, log)
        
        cursor.close()
        conn.close()
        success = True
    except Exception as E:
        log.exception(E)
        log.error(E)
        success = False
    
    if success:
        update_last_tl_version(settings, version, log)
    
    
pass
#===========================================================
# main:

def execute_patches(root_path, log):
    """executes all patching
    """
    users = get_users(root_path, log)
    patch_config(root_path, users, log)
    

def prepare_fresh_file_for_debugging(settings, log):
    """for tests during development, reset database and 
    """
    import shutil
    if not settings["modus"] == "debugging":
        raise ValueError("Modus is '{}', not 'debugging' => will not replace database!".format(settings["modus"]))
    
    log.info("Resetting data.db and config file for debugging...")
    log.info("\tdata.db...")
    login_dir = settings["login_dir"]
    db_file = os.path.join(login_dir, "data.db")
    os.remove(db_file)
    shutil.copy(os.path.join(login_dir, "data_old.db"), os.path.join(login_dir, "data.db"))
    
    log.info("\tconfig.ini...")
    update_last_tl_version(settings, "2.1.0", log)
    log.info("\t=> Done")
    
    
    

if __name__ == '__main__':
    import GUI_login
    from __init__ import __version__
    
    log = general.start_log(level="DEBUG")
    log.info("<Start patches.py>")
#     app = QApplication(sys.argv)
#     cf = GUI_login.get_basic_cf()
#     root_path = cf.get("Paths", "root_path")
#     patchme = check_patching_necessary(log)
#     if patchme:
#         request_user_input(root_path, app, log)
#         execute_patches(root_path, log)

    settings = GUI_login.get_settings("admin", log)
    prepare_fresh_file_for_debugging(settings, log)
    patch_database(settings, __version__, log)
    
    log.info("<End patches.py>")
    
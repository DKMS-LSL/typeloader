#!/usr/bin/env python3
# -*- coding: cp1252 -*-
'''
Created on 13.03.2018

general.py

contains general functions


@author: Bianca Schoene
'''

# import modules:
import sys, os, datetime, shutil, platform
from collections import defaultdict
from PyQt5.QtGui import QFont
from __init__ import __version__
import GUI_stylesheet as stylesheet
#===========================================================
# parameters & settings:

log_file = r"typeloader_GUI.log"

# QT settings:
label_style_normal = "QLabel {default}"
label_style_main = "QLabel { font-weight: bold; font-size: 12pt }"
label_style_2nd = "QLabel { font-weight: bold; font-size: 10pt }"
label_style_entry = "QLabel {background: white; border: 1 px black}"
label_style_attention = "QLabel {background: DKMSyellow}".replace("DKMSyellow", stylesheet.color_dic["DKMSyellow"])

btn_style_normal = "QPushButton {default}"
btn_style_clickme = "QPushButton {background: DKMSyellow; font-weight: bold}".replace("DKMSyellow", stylesheet.color_dic["DKMSyellow"])
btn_style_ready = "QPushButton {background: DKMSgreen; font-weight: bold}".replace("DKMSgreen", stylesheet.color_dic["DKMSgreen"])

groupbox_style_normal = "QGroupBox {default}"
groupbox_style_inactive = "QGroupBox {background: #F2F2F2}" # light grey background

line_style_normal = "QLineEdit {default}"
line_style_inactive = "QLineEdit {background: #F2F2F2}" # light grey background
line_style_changeme = "QLineEdit {background: DKMSyellow}".replace("DKMSyellow", stylesheet.color_dic["DKMSyellow"])

font_bold = QFont()
font_bold.setBold(True)
            

# allele status:
done = ["ipd accepted", "abandoned", "ipd released", "original result corrected"]
pending = ["ena submitted", "ipd submitted"]
todo = ["detected", "processing in lab", "lab process completed", "ena-ready", "ena accepted"]
error = ["ena-problem", "ipd-problem"]

allele_status_dic = defaultdict(lambda: "none")
for (category, mylist) in [("done", done), ("pending", pending), ("todo", todo), ("error", error)]:
    for status in mylist:
        allele_status_dic[status] = category

# lab status:
lab_done = ["aborted", "completed"]
lab_todo = ["repeat", "repeat original dna", "ongoing", "not started"]
lab_pending = ["on hold"]

lab_status_dic = defaultdict(lambda: "none")
for (category, mylist) in [("done", lab_done), ("todo", lab_todo), ("pending", lab_pending)]:
    for status in mylist:
        lab_status_dic[status] = category

icon_dic = {"done" : os.path.join('icons', 'done4.png'),
            "pending" : os.path.join('icons', 'pending4.png'),
            "todo" : os.path.join('icons', 'todo3.png'),
            "error" : os.path.join('icons', 'error.png')}

color_dic = {"done": stylesheet.color_dic["DKMSgreen"],
             "pending": stylesheet.color_dic["grey"],
             "todo": stylesheet.color_dic["DKMSyellow"],
             "error" : stylesheet.color_dic["DKMSred"],
             "none": stylesheet.color_dic["white"]}


field_options = {"goal" : ["novel", "extend", "confirm"],
                 "allele_status" : [status.replace("ena","ENA").replace("ipd", "IPD") for status in sorted(allele_status_dic.keys())],
                 "lab_status" : [status.replace("dna","DNA") for status in sorted(lab_status_dic.keys())],
                 "yesno" : ["yes", "no", ""],
                 "SR tech" : ["Illumina", ""],
                 "LR tech" : ["PacBio SRII", "Sequel", "ONT", ""],
                 "software_old" : ["neXtype", ""],
                 "software_new" : ["DR2S", "NGSEngine", ""],
                 "ref_db" : ["IPD-IMGT/HLA", "IPD-KIR", ""],
                 "new_confirmed" : ["new", "confirmed", ""]
                 }

if platform.system() == "Windows":
    favicon = os.path.join('icons','TypeLoader.ico')
else:
    favicon = os.path.join('icons','TypeLoader_16.png')

#TODO: (future) handle status cleanly via db tables!

# for fasta header
header_translation_dic = {"locus" : "GENE",
                          "LIMS_DONOR_ID" : "SAMPLE_ID_INT",
                          "Spendernummer" : "SAMPLE_ID_EXT",
                          "notes" : "comment",
                          "short_read_data" : "sr_data",
                          "short_read_type" : "sr_tech",
                          "long_read_phasing" : "lr_phasing",
                          "short_read_phasing" : "sr_phasing",
                          "long_read_data" : "lr_data",
                          "long_read_type" : "lr_tech",
                          "software": "new_software",
                          "version" : "new_version",
                          "date" : "new_timestamp"
                          }
#===========================================================
# classes:


#===========================================================
# functions:

def start_log(include_lines = False, error_to_email = False, info_to_file = False,
              debug_to_file = False,
              elaborate = False, level = "DEBUG"):
    """starts a logger and returns it for logging,
    if log file is wanted, info_to_file should be the log file destination (path/filename);
    default logging level is set to DEBUG
    """
    import logging.handlers, socket
    
    script_name = os.path.basename(__file__)
    log = logging.getLogger(script_name)
    
    # set level:
    level = level.upper()
    if level == "DEBUG":
        log.setLevel(logging.DEBUG)
    elif level == "INFO":
        log.setLevel(logging.INFO)
    elif level == "WARNING":
        log.setLevel(logging.WARNING)
    elif level == "ERROR":
        log.setLevel(logging.ERROR)
    elif level == "CRITICAL":
        log.setLevel(logging.CRITICAL)
    else:
        log.setLevel(logging.DEBUG)
        log.warning("Unknown loglevel '%s'! Using DEBUG instead..." % level)
    
    # define logging format:
    if include_lines:
        formatter = logging.Formatter('%(levelname)s [%(asctime)s] - [ln.%(lineno)d] %(message)s')
    elif elaborate:
        formatter = logging.Formatter("[%(asctime)s] %(levelname)s [%(filename)s:%(lineno)s - %(funcName)s] %(message)s")
    else:
        formatter = logging.Formatter('%(levelname)s [%(asctime)s] - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        
    # establish stream handler (instead of print):
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    log.addHandler(stream_handler)
    
    # establish email handler, if needed: (level ERROR)  
    if error_to_email:    
        myport = 25
        myserver = '192.168.2.23'
        nodename = socket.gethostname()
        email_adresses = ['schoene@dkms-lab.de']
        email_handler = logging.handlers.SMTPHandler(mailhost=(myserver, myport),
                                               fromaddr='%s@%s' % (script_name, nodename),
                                               toaddrs=email_adresses,
                                               subject='Error in %s' % script_name)
        email_handler.setFormatter(formatter)
        email_handler.setLevel(logging.ERROR)
        log.addHandler(email_handler)
    
    # establish file handler, if needed: (level INFO)
    if info_to_file:
        file_handler = logging.FileHandler(info_to_file)
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.INFO)
        log.addHandler(file_handler)
    
    if debug_to_file:
        log.debug_handler = logging.FileHandler(debug_to_file)
        log.debug_handler.setFormatter(formatter)
        log.debug_handler.setLevel(logging.DEBUG)
        log.addHandler(log.debug_handler)
    
    return log

def timestamp(date_format = "%Y%m%d_%H-%M"):
    """returns current date and time as short string, useable in file names etc
    """
    now = datetime.datetime.now()
    timestamp = now.strftime(date_format)
    return timestamp

def get_file_creation_date(myfile, settings, log, time_format = "%Y-%m-%d"):
    """returns a file's creation timestamp as string;
    source: https://stackoverflow.com/questions/237079/how-to-get-file-creation-modification-date-times-in-python/39501288#39501288
    """
    log.debug("Retrieving timestamp from file {}...".format(myfile))
    if settings["os"] == 'Windows':
        raw_timestamp = os.path.getctime(myfile)
    else:
        stat = os.stat(myfile)
        try:
            raw_timestamp = stat.st_birthtime
        except AttributeError:
            # We're probably on Linux. No easy way to get creation dates here,
            # so we'll settle for when its content was last modified.
            raw_timestamp = stat.st_mtime
    
    timestamp = datetime.datetime.fromtimestamp(raw_timestamp)
    timestamp_string = timestamp.strftime(time_format)
    return timestamp_string
    
def confirm(message=None, default=False, log = None):
    """prompts for yes or no response from the user. Returns True for yes and
    False for no.
    'default' should be set to the default value assumed by the caller when
    user simply types ENTER, and is marked in the prompt with square brackets.
    """
    if message is None:
        message = 'Confirm?'

    if default:
        message = '%s [y]|n: ' % (message) # default answer = yes
    else:
        message = '%s y|[n]: ' % (message) # default answer = no
        
    while True:
        answer = input(message)
        if log:
            log.info(">>>{}: [{}]".format(message, answer))
        if not answer:
            return default
        if answer not in ['y', 'Y', 'n', 'N']:
            print ('Please enter y or n!')
            continue
        if answer == 'y' or answer == 'Y':
            return True
        if answer == 'n' or answer == 'N':
            return False

def move_rename_file(old_path, new_dir, new_name):
    """moves a file from old_path to new_dir & renames it to <new_name>.<all old extensions>,
    returns new path
    """
    if old_path.endswith(".blast.xml"):
        ext = ".blast.xml"
    else:
        ext = os.path.splitext(old_path)[-1]
    new_path = os.path.join(new_dir, new_name + ext)
    print (new_path)
    try:
        shutil.move(old_path, new_path)
    except:
        print(old_path)
        print(new_path)
        shutil.move(old_path, new_path)
    return new_path


def delete_sample():
    pass
    
pass
#===========================================================
# main:

def main(log):
    pass

if __name__ == "__main__":
    import GUI_login
    log = start_log(level="DEBUG")
    log.info("<Start {} V{}>".format(os.path.basename(__file__), __version__))
    settings_dic = GUI_login.get_settings("admin", log)
    myfile = os.path.join("tables", "alleles.csv")
    print (get_file_creation_date(myfile, settings_dic, log))
    main(log)
    log.info("<End>")

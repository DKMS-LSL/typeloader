#!/usr/bin/env python3
# -*- coding: cp1252 -*-
'''
Created on 19.07.2018

GUI_forms_new_allele_bulk.py

a dialog to upload sequence fastas to TypeLoader as bulk

@author: Bianca Schoene
'''

# import modules:

import sys, os

from PyQt5.QtWidgets import (QApplication, QMessageBox, QTextEdit,
                             QPushButton, QHBoxLayout)
from PyQt5.Qt import QWidget, pyqtSlot, pyqtSignal
from PyQt5.QtGui import QIcon

import general, typeloader_functions as typeloader, db_internal

from GUI_forms import (CollapsibleDialog, ChoiceSection, 
                       FileButton, ProceedButton, QueryButton, NewProjectButton)
from GUI_misc import settings_ok

#===========================================================
# parameters:
min_num_prev_alleles = 5 # this many alleles have to be added manually before using bulk upload

#===========================================================
# classes:

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
    

class NewAlleleBulkForm(CollapsibleDialog):
    """a popup widget to submit new Typeloader target alleles as bulk upload
    """
    refresh_project = pyqtSignal(str)
        
    def __init__(self, log, mydb, current_project, settings, parent = None):
        self.log = log
        self.mydb = mydb
        self.current_project = current_project
        self.settings = settings
        super().__init__(parent)
        self.log.debug("Opening 'New Allele Bulk Upload' Dialog...")
        self.raw_path = None
        self.project = None
        self.resize(800,300)
        self.setWindowTitle("Add new target alleles (bulk fasta upload)")
        self.setWindowIcon(QIcon(general.favicon))
        
        self.show()
        ok, msg = settings_ok("new", self.settings, self.log)
        if not ok:
            QMessageBox.warning(self, "Missing settings", msg)
            self.close()
            
        proceed = self.check_newbie_proceed()
        if not proceed:
            self.close()
        
    def define_sections(self):
        """defining the dialog's sections
        """
        self.define_section1()
        self.define_section2()
    
    def define_section1(self):
        """defining section 1: choose file to upload and project
        """
        mywidget = QWidget(self)
        layout = QHBoxLayout()
        mywidget.setLayout(layout)
        
        mypath = self.settings["raw_files_path"]
        file_btn = FileButton("Choose .csv file with target allele fasta files", mypath, self)
        self.file_widget = ChoiceSection("Raw File:", [file_btn], self.tree)
        self.file_widget.choice.connect(self.get_file)
        if self.settings["modus"] == "debugging":
            self.file_widget.field.setText(r"H:\Projekte\Bioinformatik\Typeloader\example files\bulk_upload3.csv")
        layout.addWidget(self.file_widget)
        
        proj_btn = QueryButton("Choose a (different) existing project", "SELECT project_name FROM projects where project_status = 'Open' order by project_name desc") 
        new_proj_btn = NewProjectButton("Start a new project", self.log, self.mydb, self.settings)
        self.proj_widget = ChoiceSection("Project:", [proj_btn, new_proj_btn], self.tree)
        self.proj_widget.field.setText(self.current_project)
        proj_btn.change_to_normal(None)
        new_proj_btn.change_to_normal(None)
        
        self.proj_widget.choice.connect(self.get_project)
        layout.addWidget(self.proj_widget)
        
        self.upload_btn = ProceedButton("Upload", [self.file_widget.field, self.proj_widget.field], self.log, 0)
        layout.addWidget(self.upload_btn)
        self.file_widget.choice.connect(self.upload_btn.check_ready)
        self.proj_widget.choice.connect(self.upload_btn.check_ready)
        self.upload_btn.proceed.connect(self.perform_bulk_upload)
        
        self.sections.append(("(1) Upload bulk-submission file:", mywidget))
        
    @pyqtSlot(str)
    def get_file(self, file_path):
        """catches name of the file chosen in section1
        """
        self.csv_file = file_path
        self.log.debug("Chose file {}...".format(self.raw_path))

    @pyqtSlot(str)
    def get_project(self, project):
        """catches name of the project chosen in section1
        """
        self.project = project.strip()
        self.log.debug("Chose project {}...".format(self.project))
    
    @pyqtSlot()
    def confirm_upload(self):
        msg = "Are you really sure you want to upload all these alleles at once?\n"
        msg += "This will likely take several minutes.\n\n"
        msg += "(This box will stay here while your upload is processed, please don't re-click your choice.)"
        reply = QMessageBox.question(self, 'Confirm bulk upload', msg, QMessageBox.Yes | 
            QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            return True
        else:
            return False
        
    @pyqtSlot()
    def perform_bulk_upload(self, auto_confirm = False):
        """parses chosen file & uploads all alleles
        """
        if not auto_confirm:
            confirmed = self.confirm_upload()
            if not confirmed:
                return
            
        self.project = self.proj_widget.field.text().strip()
        self.csv_file = self.file_widget.field.text().strip()
        
        try:
            report, self.errors_found = typeloader.bulk_upload_new_alleles(self.csv_file, self.project, 
                                                                           self.settings, self.mydb, self.log)
            self.report_txt.setText(report)
            self.upload_btn.setChecked(False)
        except Exception as E:
            self.log.error(E)
            self.log.exception(E)
            QMessageBox.warning(self, "Unexpected problem!", "An unexpected error occurred during bulk upload:\n\n{}".format(repr(E)))
        
        self.ok_btn.setStyleSheet(general.btn_style_ready)
        self.ok_btn.setEnabled(True)
        self.proceed_sections(0, 1)
        self.refresh_project.emit(self.project)
        return True
        
        
    def define_section2(self):
        """defining section 2: shows errors
        """
        mywidget = QWidget(self)
        layout = QHBoxLayout()
        mywidget.setLayout(layout)
        
        self.report_txt = QTextEdit(self)
        layout.addWidget(self.report_txt)
        
        self.ok_btn = QPushButton("Ok", self)
        layout.addWidget(self.ok_btn)
        self.ok_btn.clicked.connect(self.close)
        
        self.sections.append(("(2) Check results:", mywidget))


    def check_newbie_proceed(self):
        """checks if this user has already uploaded enough single alleles to count as experienced;
        if not, a popup warning is generated and bulk upload denied
        """
        if self.settings["modus"] == "staging":
            return True
        
        self.log.debug("Checking if this user is experienced enough...")
        query = "select count(local_name) from alleles"
        success, data = db_internal.execute_query(query, 1, self.log, "Checking for previous uploads", "Database error", self)
        if not success:
            return False
        if data:
            num = data[0][0]
        else:
            num = 0
        if num < min_num_prev_alleles:
            self.log.info("=> User is not experienced enough, yet!")
            msg = "Bulk Fasta upload is for experienced TypeLoader users.\n\n"
            msg += "Please upload at least {} alleles using single Fasta or XML files,\n".format(min_num_prev_alleles)
            msg += "to make sure you are sufficiently familiar with TypeLoader."
            QMessageBox.warning(self, "Hello new user", msg)
            return False
        self.log.info("=> Experienced user")
        return True
        

pass
#===========================================================
# main:
        
if __name__ == '__main__':
    from typeloader_GUI import create_connection, close_connection
    import GUI_login
    log = general.start_log(level="DEBUG")
    log.info("<Start {}>".format(os.path.basename(__file__)))
    sys.excepthook = log_uncaught_exceptions
    mysettings = GUI_login.get_settings("staging", log)
    mydb = create_connection(log, mysettings["db_file"])
    
    app = QApplication(sys.argv)
    project = "20190319_STG_mixed_test"
    ex = NewAlleleBulkForm(log, mydb, project, mysettings)
#     ex = QueryBox(log, mysettings)
    ex.show()
    
    result = app.exec_()
    close_connection(log, mydb)
    log.info("<End>")
    sys.exit(result)
#     sys.exit(app.exec_())


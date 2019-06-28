#!/usr/bin/env python3
# -*- coding: cp1252 -*-
'''
Created on 13.03.2018

GUI_forms.py

widgits for adding new sequences or new projects to TypeLoader

@author: Bianca Schoene
'''

# import modules:

import sys, os, time
from PyQt5.QtWidgets import (QApplication, QMessageBox, QTextEdit, QPushButton, 
                             QTableWidget, QHBoxLayout, QTableWidgetItem)
from PyQt5.Qt import QWidget, pyqtSlot, pyqtSignal
from PyQt5.QtGui import QIcon

import general, db_internal
from GUI_forms import (CollapsibleDialog, ChoiceSection, 
                       ProceedButton, QueryButton, FileChoiceTable)
from GUI_misc import settings_ok
from typeloader_functions import create_ENA_filenames, submit_sequences_to_ENA_via_CLI

#===========================================================
# parameters:

from __init__ import __version__
#===========================================================
# classes:

class ProjectInfoTable(QTableWidget):
    """display all info about one project
    """
    updated = pyqtSignal()
    project_info = pyqtSignal(str, str) # (title, description)
    
    def __init__(self, project, log, parent = None):
        super().__init__(parent)
        self.log = log
        if parent:
            self.settings = parent.settings
        else:
            import GUI_login
            self.settings = GUI_login.get_settings("admin", self.log)
        self.init_UI()
        
    def init_UI(self):   
        self.setRowCount(4)
        self.setColumnCount(1)
        header = ["Project Name:", "Accession Nr.:", "Files:", "Chosen:"]
        self.setVerticalHeaderLabels(header)
        self.horizontalHeader().hide()
        self.horizontalHeader().setStretchLastSection(True)
        self.setItem(2,0, QTableWidgetItem(""))
        self.setItem(3,0, QTableWidgetItem(""))
        
    def fill_UI(self, project):
        self.setItem(0,0, QTableWidgetItem(project))
        query = "select ENA_ID_project, title, description from projects where project_name = '{}'".format(project)
        try:
            success, data = db_internal.execute_query(query, 3, self.log, 
                                                      "getting project data from database", 
                                                      "Database error", self)
            if success:
                self.ENA_ID = data[0][0]
                title = data[0][1]
                desc = data[0][2]
                self.log.debug("ProjectInfoTable emitted project_info = ('{}','{}')".format(title, desc))
                self.project_info.emit(title, desc)
            else:
                self.log.warning("GUI_forms_submission_ENA.ProjectInfoTable.fill_UI() had a problem!")
                self.ENA_ID = ""
        except IndexError: # happens if no project is given at start
            self.ENA_ID = ""
            
        self.setItem(1,0, QTableWidgetItem(self.ENA_ID))
        
        self.resizeColumnsToContents()
    
    @pyqtSlot(int)
    def update_files(self, nr):
        """updates the "number of files" field
        """
        self.log.debug("Setting files to {}".format(nr))
        try:
            self.item(2,0).setText(str(nr))
        except AttributeError:
            myitem = QTableWidgetItem(str(nr))
            if nr == 0:
                myitem.setBackground(general.color_dic["todo"])
            self.setItem(2,0, myitem)
        self.updated.emit()
    
    @pyqtSlot(int)    
    def update_files_chosen(self, nr):
        """updates the "number of files chosen" field
        """
        self.log.debug("Setting chosen_files to {}".format(nr))
        try:
            self.item(3,0).setText(str(nr))
        except AttributeError:
            myitem = QTableWidgetItem(str(nr))
            if nr == 0:
                myitem.setBackground(general.color_dic["todo"])
            self.setItem(3,0, myitem)  
        self.updated.emit()
    
        
class ENAFileChoiceTable(FileChoiceTable):
    """displays all alleles of a project
    so user can choose which to submit to ENA
    """
    def __init__(self, project, log, parent = None):
        query = """select project_nr, alleles.sample_id_int, ena_file, allele_status 
        from alleles
         join files on alleles.sample_id_int = files.sample_id_int and alleles.allele_nr = files.allele_nr
        """.format(project)
        num_columns = 4
        header = ["Submit?", "Nr", "Sample", "File", "Allele Status"]
        if parent:
            self.settings = parent.settings
        else:
            import GUI_login
            self.settings = GUI_login.get_settings("admin", log)
        
        super().__init__(project, log, header, query, num_columns, 
                         myfilter = "", allele_status_column = 3, instant_accept_status = "ENA-ready",
                         parent = self)
    
    def refresh(self, project):
        self.myfilter = " where alleles.project_name = '{}' order by project_nr".format(project)
        self.fill_UI()
        
        
class ENASubmissionForm(CollapsibleDialog):
    """a popup widget to upload alleles of a project to ENA
    """
    ENA_submitted = pyqtSignal()
    change_project = pyqtSignal(str, str)
    
    def __init__(self, log, mydb, project, settings, parent = None):
        self.log = log
        self.log.debug("Opening 'ENA Submission' Dialog...")
        self.mydb = mydb
        self.project = project
        self.settings = settings
        super().__init__(parent)
        
        self.resize(900,500)
        self.setWindowTitle("Submit alleles to ENA")
        self.setWindowIcon(QIcon(general.favicon))
        self.samples = []
        self.choices = {}
        self.ENA_response = ""
        self.title = ""
        self.description = ""
        self.submission_successful = False
        self.accepted = True
        self.problem_samples = []
        self.show()
        
        ok, msg = settings_ok("ENA", self.settings, self.log)
        if not ok:
            QMessageBox.warning(self, "Missing ENA settings", msg)
            self.close()
    
    def define_sections(self):
        """defining the dialog's sections
        """
        self.define_section1()
        self.define_section2()
        self.define_section3()
    
    def define_section1(self):
        """defining section 1: choose project
        """
        mywidget = QWidget(self)
        layout = QHBoxLayout()
        mywidget.setLayout(layout)
        
        proj_btn = QueryButton("Choose a (different) existing project", "SELECT project_name FROM projects where project_status = 'Open' order by project_name desc") 
        self.proj_widget = ChoiceSection("Project:", [proj_btn], self.tree)
        self.proj_widget.field.setText(self.project)
        if self.project:
            proj_btn.change_to_normal(None)
        
        layout.addWidget(self.proj_widget)
        
        self.ok_btn = ProceedButton("Proceed", [self.proj_widget.field], self.log, 0)
        layout.addWidget(self.ok_btn)
        self.proj_widget.choice.connect(self.ok_btn.check_ready)
        self.ok_btn.proceed.connect(self.proceed_to2)
        
        self.sections.append(("(1) Choose project:", mywidget))
    
    @pyqtSlot(int)
    def proceed_to2(self, _):
        """proceed to next section
        """
        self.project = self.proj_widget.field.text()
        self.refresh_section2()
        self.proceed_sections(0, 1)
        
    def refresh_section2(self):
        """refreshes data in section2 after project has been changed
        """
        self.log.debug("Refreshing section 2...")
        self.project_info.fill_UI(self.project)
        try:
            self.project_files.refresh(self.project)
        except Exception as E:
            self.log.exception(E)
        
    def define_section2(self, initial = True):
        """defining section 2: choose alleles
        """
        self.log.debug("Setting up section2 of ENASubmissionForm...")
        mywidget = QWidget(self)
        layout = QHBoxLayout()
        mywidget.setLayout(layout)
        mywidget.setMinimumHeight(250)
        self.project_info = ProjectInfoTable(self.project, self.log, self)
        self.project_info.setMaximumWidth(300)
        self.project_info.setMinimumWidth(200)
        layout.addWidget(self.project_info)
        self.project_info.project_info.connect(self.catch_project_info)
        
        self.project_files = ENAFileChoiceTable(self.project, self.log, self)
        layout.addWidget(self.project_files)
        self.project_files.files_chosen.connect(self.project_info.update_files_chosen)
        self.project_files.files.connect(self.project_info.update_files)
        
        items = [self.project_info.item(3,0)]
        self.submit_btn = ProceedButton("Submit to ENA", items, self.log, 1, self)
        self.submit_btn.proceed.connect(self.submit_to_ENA)
        self.submit_btn.setMinimumWidth(100)
        layout.addWidget(self.submit_btn)
        self.project_info.updated.connect(self.submit_btn.check_ready)
        
        self.sections.append(("(2) Choose alleles to submit:", mywidget))
    
    def catch_project_info(self, title, description):
        """catches title & description emitted by ProjectInfoTable
        """
        self.title = title
        self.description = description
 
    def check_first_time_proceed(self):
        """checks if this is this user's first ENA submission;
        if yes, asks for confirmation before proceeding
        """
        if self.settings["embl_submission"] == self.settings["embl_submission_prod"]:
            self.log.debug("Checking if this is your first ENA submission...")
            query = "select submission_id from ena_submissions where success = 'yes' LIMIT 1"
            success, data = db_internal.execute_query(query, 1, self.log, "Checking for previous ENA submissions", "Database error", self)
            if not success:
                return False
            if data:
                return True
            else: # first productive submission
                self.log.info("First submission to ENA's productive server. Proceed?")
                msg = "This user has never before submitted to ENA's productive server.\n"
                msg += "If you have not tried this out using a test user, you really should.\n"
                msg += "(See user manual under 'Test Users' for details.)\n\n"
                msg += "Do you want to proceed?"
                reply = QMessageBox.question(self, "First real ENA submission",
                                        msg, QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if reply == QMessageBox.Yes:
                    self.log.info("\t=> Proceed!")
                    return True
                else:
                    self.log.info("\t=> I'd rather not.")
                    return False
        else: # if connected to TEST server, proceed
            self.log.debug("Sending to ENA's test server...")
            return True
    
    def submit_to_ENA(self, _):
        """submit the selected alleles to ENA & proceed to next section
        """
        proceed = self.check_first_time_proceed()
        if not proceed:
            self.submit_btn.setChecked(False)
            return
        
        self.project_name = self.proj_widget.field.text()
        ENA_ID = self.project_info.ENA_ID
        
        projects_dir = self.settings["projects_dir"]
        
        self.accepted = False
        
        files = []
        j = 0
        for i in self.project_files.check_dic:
            box = self.project_files.check_dic[i]
            if box.checkState():
                nr = self.project_files.item(i, 1).text()
                sample = self.project_files.item(i, 2).text()
                file = self.project_files.item(i, 3).text()
                files.append(os.path.join(projects_dir, self.project_name, sample, file))
                cell_line = file.split(".")[0]
                self.samples.append([self.project_name, nr])
                self.choices[j] = [self.project_name, nr, sample, cell_line]
                j += 1
        
        try:
            self.submission_successful = True
            self.file_dic, curr_time, analysis_alias = create_ENA_filenames(self.project_name, ENA_ID, self.settings, self.log)
            self.ena_results, success, err_type, msg, self.problem_samples = submit_sequences_to_ENA_via_CLI(self.project_name, ENA_ID, 
                                                                            analysis_alias, curr_time, 
                                                                            self.samples, files, self.file_dic, 
                                                                            self.settings, self.log)

            if self.ena_results: # files were created and we got a reply from ENA, positive or negative
                self.textbox.setText(self.ena_results[-1])
            
                if not success:
                    self.submission_successful = False
                    self.cleanup_submission_failed()
                self.proceed_sections(1,2)
            
            else:
                QMessageBox.warning(self, err_type, msg)
                self.submission_successful = False
                self.cleanup_submission_failed()
                
        except Exception as E:
            self.log.exception(E)
            QMessageBox.warning(self, "ENA submission failed", 
                                "An error occured during ENA submission:\n\n{}".format(repr(E)))
            self.submission_successful = False
            self.cleanup_submission_failed()
                                        
    def cleanup_submission_failed(self):
        """deletes old files after submission failed
        """
        self.log.debug("Deleting old files after failed submission...")
        for key in self.file_dic:
            myfile = self.file_dic[key]
            try:
                (path, ext) = os.path.splitext(myfile)
                if ext == ".gz":
                    (path, ext1) = os.path.splitext(path)
                    ext = ext1 + ext
                if not os.path.isdir(myfile):
                    new_path = path + "_failed" + ext
                    os.rename(myfile, new_path)
            except IOError:
                pass
        self.submit_btn.setChecked(False)
        self.accepted = True
        self.log.debug("\t=> Done")
            
    def define_section3(self):
        """defining section 3: ENA response
        """
        mywidget = QWidget(self)
        layout = QHBoxLayout()
        mywidget.setLayout(layout)
        
        self.textbox = QTextEdit(self)
        layout.addWidget((self.textbox))
        
        self.close_btn = QPushButton("OK", self)
        layout.addWidget(self.close_btn)
        self.close_btn.clicked.connect(self.save_to_db)
        
        self.sections.append(("(3) Check ENA's response", mywidget))
    
    def save_to_db(self):
        """updates database with results of ENA submission
        """
        self.log.info("Saving submission results to database...")
        update_queries = []
        if self.submission_successful:
            self.log.debug("Saving changes to db...")
            (submission_id, timestamp_sent, timestamp_confirmed, acc_analysis,
             acc_submission, self.ENA_response) = self.ena_results
            
            # update allele_status for individual alleles:
            for [project_name, nr] in self.samples:
                query = """update alleles set allele_status = 'ENA submitted', ena_submission_id = '{}'
                    where project_name = '{}' and project_nr = {}""".format(submission_id, project_name, nr)
                update_queries.append(query)
            
            # update ENA_submissions table:
            query2 = """insert into ena_submissions 
            (PROJECT_NAME, SUBMISSION_ID, NR_ALLELES, TIMESTAMP_SENT, 
            TIMESTAMP_CONFIRMED, ACC_ANALYSIS, ACC_SUBMISSION, SUCCESS) values
            ('{}', '{}', {}, '{}',
            '{}', '{}', '{}', 'yes')""".format(self.project_name, submission_id,
                                            len(self.samples), timestamp_sent,
                                            timestamp_confirmed, acc_analysis,
                                            acc_submission) 
            update_queries.append(query2)
            
        else:
            # update allele_status for individual alleles:
            for i in self.problem_samples:
                [project, nr, _, _] = self.choices[i] 
                query3 = """update alleles set allele_status = 'ENA-problem'
                    where project_name = '{}' and project_nr = {}""".format(project, nr)
                update_queries.append(query3)
                
        success = db_internal.execute_transaction(update_queries, self.mydb, self.log, 
                                                  "saving the results to the internal db", 
                                                  "Database error", self)   
        if success:
            self.ENA_submitted.emit()
            self.change_project.emit(self.project_name, "Open")
            self.accepted = True
            self.close()
    
    def closeEvent(self, event):
        """checks for unaccepted ENA results before closing
        """
        if not self.accepted:
            QMessageBox.warning(self, "Unaccepted changes!", "Please accept the ENA result by clicking 'OK' before closing!")
            event.ignore()
        
        else:
            self.log.debug("Closing ENASubmissionForm...")
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
        
if __name__ == '__main__':
    from typeloader_GUI import create_connection, close_connection
    import GUI_login
    sys.excepthook = log_uncaught_exceptions
    log = general.start_log(level="DEBUG")
    log.info("<Start {} V{}>".format(os.path.basename(__file__), __version__))
    settings_dic = GUI_login.get_settings("admin", log)
    mydb = create_connection(log, settings_dic["db_file"])
    
    app = QApplication(sys.argv)
    ex = ENASubmissionForm(log, mydb, "20190627_ADMIN_mixed_ENA-Test", settings_dic)
    ex.show()
    
    result = app.exec_()
    close_connection(log, mydb)
    log.info("<End>")
    sys.exit(result)
#     sys.exit(app.exec_())


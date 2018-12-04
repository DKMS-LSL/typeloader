#!/usr/bin/env python3
# -*- coding: cp1252 -*-
'''
Created on 13.03.2018

GUI_forms.py

components for forms and dialogs

@author: Bianca Schoene
'''

# import modules:

import sys, os, shutil, time
from shutil import copyfile
from PyQt5.QtWidgets import (QApplication, QFileDialog, QGridLayout,
                             QPushButton, QMessageBox, QTextEdit,
                             QWidget, QHBoxLayout)
from PyQt5.Qt import pyqtSlot, pyqtSignal
from PyQt5.QtGui import QIcon

import general, db_internal
from typeloader_core import make_imgt_files as MIF
from GUI_forms import (CollapsibleDialog, ChoiceSection, FileChoiceTable,
                       FileButton, ProceedButton, QueryButton)
from GUI_forms_submission_ENA import ProjectInfoTable
from GUI_misc import settings_ok

#===========================================================
# parameters:

from __init__ import __version__
#===========================================================
# classes:
    
class IPDFileChoiceTable(FileChoiceTable):
    """displays all alleles of a project
    so user can choose which to submit to IPD
    """
    def __init__(self, project, log, parent = None):
        query = """select project_nr, alleles.sample_id_int, alleles.cell_line, allele_status, 
        ENA_submission_id, IPD_submission_nr
        from alleles
         join files on alleles.sample_id_int = files.sample_id_int and alleles.allele_nr = files.allele_nr
        """.format(project)
        num_columns = 6
        header = ["Submit?", "Nr", "Sample", "Cell Line", "Allele Status", "ENA submission ID", "IPD submission ID"]
        if parent:
            self.settings = parent.settings
        else:
            import GUI_login
            self.settings = GUI_login.get_settings("admin", log)
        
        super().__init__(project, log, header, query, num_columns,
                         myfilter = "", allele_status_column = 3, 
                         instant_accept_status = "ENA submitted", parent = self)
    
    def refresh(self, project, addfilter):
        self.myfilter = " where alleles.project_name = '{}' {} order by ENA_submission_id, project_nr".format(project, addfilter)
        self.fill_UI()
        
        
class IPDSubmissionForm(CollapsibleDialog):
    """a popup widget to upload alleles of a project to IPD
    """
    IPD_submitted = pyqtSignal()
    
    def __init__(self, log, mydb, project, settings, parent = None):
        self.log = log
        self.log.info("Opening 'IPD Sumbission' Dialog...")
        self.mydb = mydb
        self.project = project
        self.settings = settings
        self.label_width = 150
        super().__init__(parent)
        
        self.resize(1150,500)
        self.setWindowTitle("Submit alleles to IPD")
        self.setWindowIcon(QIcon(general.favicon))
        self.samples = []
        self.file_dic = {}
        self.add_filter = ""
        self.title = ""
        self.description = ""
        self.imgt_files = {}
        self.submission_successful = False
        self.accepted = False
        self.show()
        ok, msg = settings_ok("IPD", self.settings, self.log)
        if not ok:
            QMessageBox.warning(self, "Missing IPD settings", msg)
            self.close()
        
    def define_sections(self):
        """defining the dialog's sections
        """
        self.define_section1()
        self.define_section2()
        self.define_section3()
        self.define_section4()
    
    def define_section1(self):
        """defining section 1: choose project & ENA file
        """
        mywidget = QWidget(self)
        layout = QHBoxLayout()
        mywidget.setLayout(layout)
        
        proj_btn = QueryButton("Choose a (different) existing project", "SELECT project_name FROM projects where project_status = 'Open' order by project_name desc") 
        self.proj_widget = ChoiceSection("Project:", [proj_btn], self.tree, label_width=self.label_width)
        if self.project:
            self.proj_widget.field.setText(self.project)
            proj_btn.change_to_normal(None)
        
        layout.addWidget(self.proj_widget)
        
        self.ok_btn1 = ProceedButton("Proceed", [self.proj_widget.field], self.log, 0)
        layout.addWidget(self.ok_btn1)
        self.proj_widget.choice.connect(self.ok_btn1.check_ready)
        self.ok_btn1.proceed.connect(self.proceed_to2)
        self.sections.append(("(1) Choose project:", mywidget))
    
    @pyqtSlot(int)
    def proceed_to2(self, _):
        """proceed to next section
        """
        self.project = self.proj_widget.field.text()
        self.refresh_section3()
        self.proceed_sections(0, 1)
    
    def define_section2(self):
        """defining section 1: choose project & ENA file
        """
        mywidget = QWidget(self)
        layout = QGridLayout()
        mywidget.setLayout(layout)
        
        mypath = self.settings["raw_files_path"]
        ENA_file_btn = FileButton("Upload email attachment from ENA reply", mypath, parent=self)
        self.ENA_file_widget = ChoiceSection("ENA reply file:", [ENA_file_btn], self, label_width=self.label_width)
        if self.settings["modus"] == "debugging":
            self.ENA_file_widget.field.setText(r"H:\Projekte\Bioinformatik\Typeloader\example files\IPD_Test\ENA_Accession_3DP1")
            ENA_file_btn.change_to_normal()
            
        layout.addWidget(self.ENA_file_widget, 0, 0)
        
        befund_file_btn = FileButton("Choose file with pretypings for each sample", mypath, parent=self)
        self.befund_widget = ChoiceSection("Pretyping file:", [befund_file_btn], self, label_width=self.label_width)
        self.befund_widget.setWhatsThis("Choose a file containing a list of previously identified alleles for all loci for each sample")
        if self.settings["modus"] == "debugging":
            self.befund_widget.field.setText(r"H:\Projekte\Bioinformatik\Typeloader\example files\IPD_Test\Befunde_neu.csv")
            befund_file_btn.change_to_normal()
        layout.addWidget(self.befund_widget, 1, 0)
        
        self.ok_btn2 = ProceedButton("Proceed", [self.proj_widget.field, self.befund_widget.field], self.log, 0)
        self.proj_widget.choice.connect(self.ok_btn2.check_ready)
        self.befund_widget.choice.connect(self.ok_btn2.check_ready)
        layout.addWidget(self.ok_btn2, 0, 1,3,1)
        self.ok_btn2.proceed.connect(self.proceed_to3)
        self.sections.append(("(2) Upload ENA reply file:", mywidget))
    
    def parse_ENA_file(self):
        """parses the ENA reply file,
        stores results and adjusts filter for IPDFileChoiceTable
        """
        self.ENA_reply_file = self.ENA_file_widget.field.text().strip()
        self.ENA_timestamp = general.get_file_creation_date(self.ENA_reply_file, self.settings, self.log)
        self.ENA_id_map, self.ENA_gene_map = MIF.parse_email(self.ENA_reply_file)
        self.add_filter = "and alleles.cell_line in ('{}')".format("', '".join(sorted(self.ENA_id_map.keys())))
                                  
    @pyqtSlot(int)
    def proceed_to3(self, _):
        """proceed to next section
        """
        self.parse_ENA_file()
        self.refresh_section3()
        self.proceed_sections(1, 2)
        
    def refresh_section3(self):
        """refreshes data in section3 after project has been changed
        """
        self.log.debug("Refreshing section 3...")
        self.project_info.fill_UI(self.project)
        self.project_files.refresh(self.project, self.add_filter)
        
    @pyqtSlot(str, str)
    def catch_project_info(self, title, description):
        """catches title & description emitted by ProjectInfoTable
        """
        self.title = title
        self.description = description
        
    def define_section3(self):
        """defining section 3: choose alleles
        """
        self.log.debug("Setting up section3 of IPDSubmissionForm...")
        mywidget = QWidget(self)
        layout = QHBoxLayout()
        mywidget.setLayout(layout)
        mywidget.setMinimumHeight(250)
        self.project_info = ProjectInfoTable(self.project, self.log, self)
        self.project_info.setMaximumWidth(350)
        self.project_info.setMinimumWidth(250)
        layout.addWidget(self.project_info)
        self.project_info.project_info.connect(self.catch_project_info)
        
        self.project_files = IPDFileChoiceTable(self.project, self.log, self)
        layout.addWidget(self.project_files)
        self.project_files.files_chosen.connect(self.project_info.update_files_chosen)
        self.project_files.files.connect(self.project_info.update_files)
        
        items = [self.project_info.item(3,0)]
        self.submit_btn = ProceedButton("Generate IPD file", items, self.log, 1, self)
        self.submit_btn.proceed.connect(self.make_IPD_files)
        self.submit_btn.setMinimumWidth(100)
        layout.addWidget(self.submit_btn)
        self.project_info.updated.connect(self.submit_btn.check_ready)
        
        self.sections.append(("(3) Choose alleles to submit:", mywidget))
    
    def get_chosen_samples(self):
        """gets results of file choice in section2,
        stores them in self.samples
        """
        self.samples = [] 
        for i in self.project_files.check_dic:
            box = self.project_files.check_dic[i]
            if box.checkState():
                sample = self.project_files.item(i, 2).text()
                cell_line = self.project_files.item(i, 3).text()
                IPD_nr = self.project_files.item(i, 6).text()
                self.samples.append((sample, cell_line, IPD_nr))

    def get_values(self):
        """retrieves values for IPD file generation from GUI
        """
        self.pretypings = self.befund_widget.field.text().strip()
        self.project = self.proj_widget.field.text().strip()
        self.curr_time = time.strftime("%Y%m%d%H%M%S")
        self.subm_id = "IPD_{}".format(self.curr_time)
        
        return True
    
    def get_files(self):
        """retrieves ena_file and blast_xml for each chosen sample
        """
        self.file_dic = {}
        for (sample_id_int, cell_line, _) in self.samples:
            self.file_dic[cell_line] = {}
            query = """select blast_xml, ena_file from files 
            where sample_id_int = '{}' and cell_line = '{}'""".format(sample_id_int, cell_line)
            success, data = db_internal.execute_query(query, 2, self.log, 
                                "retrieving sample files", "Database error", self)
            if success:
                self.file_dic[cell_line]["blast_xml"] = data[0][0]
                self.file_dic[cell_line]["ena_file"] = data[0][1]
                    
    @pyqtSlot()
    def make_IPD_files(self):
        """tell typeloader to create the IPD file
        """
        success = self.get_values()
        if not success:
            return
        
        project_dir = os.path.join(self.settings["projects_dir"], self.project)
        mydir = os.path.join(project_dir, "IPD-submissions", self.subm_id)
        os.makedirs(mydir, exist_ok = True)
            
        try:
            for myfile in [self.ENA_reply_file, self.pretypings]:
                new_path = os.path.join(mydir, os.path.basename(myfile))
                shutil.copy(myfile, new_path)
                myfile = new_path
            
            self.log.debug("Creating IPD file...")
            self.get_chosen_samples()
            self.get_files()
            
            results = MIF.write_imgt_files(project_dir, self.samples, self.file_dic, self.ENA_id_map, 
                                           self.ENA_gene_map, self.pretypings, self.subm_id, 
                                           mydir, self.settings, self.log)
            if not results[0]:
                QMessageBox.warning(self, "IPD file creation error", results[1])
                return
            else:
                (self.IPD_file, self.cell_lines, self.customer_dic, resultText, self.imgt_files, success, error) = results
            if error:
                QMessageBox.warning(self, "IPD file creation error", "An error occurred during the creation of IPD files:\n\n{}".format(repr(error)))
                return
            if success:
                if not resultText:
                    resultText = "All genes and alleles were resolved"
                self.log.debug("Success: {}".format(resultText))
            else:
                self.log.info("IPD file creation not successful")
                QMessageBox.warning(self, "IPD file creation not successful", "Could not create IPD files!")
                return
            
        except Exception as E:
            self.log.error(E)
            self.log.exception(E)
            QMessageBox.warning(self, "IPD file creation error", "An error occured during creation of the IPD files:\n\n{}".format(repr(E)))
            return
        
        self.submission_successful = False
        if os.path.exists(self.IPD_file):
            if os.path.getsize(self.IPD_file):
                self.submission_successful = True 
        
        if self.submission_successful:
            self.log.info("=> Successfully made IPD-file: {}".format(self.IPD_file))
            self.download_btn.setEnabled(True)
            self.download_btn.setStyleSheet(general.btn_style_ready)
            self.ok_btn.setEnabled(True)
            self.sender().setChecked(False)
            self.sender().setStyleSheet(general.btn_style_normal)
            
            self.save_to_db()
            self.IPD_submitted.emit()
            self.proceed_to4()
        else:
            self.log.error("No IPD-File created!")
            QMessageBox.warning(self, "IPD file creation error", "Creation of the IPD zip file was not successful")
            
    @pyqtSlot(int)
    def proceed_to4(self):
        """proceed to next section
        """
        text = "Successfully created IPD files for {} alleles:\n".format(len(self.samples))
        for (sample, cell_line, _) in self.samples:
            text += "\t- {} ({})\n".format(cell_line, sample)
        self.textbox.setText(text)
        self.download_btn.setEnabled(True)
        self.proceed_sections(2, 3)
    
    @pyqtSlot()
    def download_IPD_file(self):
        """download the IPD file
        """
        self.log.debug("Downloading {}...".format(self.IPD_file))
        suggested_path = os.path.join(self.settings["default_saving_dir"], os.path.basename(self.IPD_file))
        chosen_path = QFileDialog.getSaveFileName(self, "Download IPD file...", suggested_path)[0]
        if chosen_path:
            copyfile(self.IPD_file, chosen_path)
        self.download_btn.setStyleSheet(general.btn_style_normal)
        self.close()
    
    @pyqtSlot()
    def save_to_db(self):
        """updates database with results of ENA submission
        """
        success = False
        if self.submission_successful:
            try:
                self.log.info("Saving changes to db...")
                update_queries = []
                for (sample, cell_line, _) in self.samples:
                    # update allele_status for individual alleles:    
                    IPD_submission_nr = self.cell_lines[cell_line]
                    update_query = """update alleles set allele_status = 'IPD submitted',
                        ENA_accession_nr = '{}', ENA_acception_date = '{}',
                        IPD_SUBMISSION_ID = '{}', IPD_SUBMISSION_NR = '{}' 
                        where cell_line = '{}'""".format(self.ENA_id_map[cell_line], self.ENA_timestamp,
                                                         self.subm_id, IPD_submission_nr, cell_line)
                    update_queries.append(update_query)
                    
                    # update files table:
                    subm_file = self.imgt_files[IPD_submission_nr]
                    update_files_query = """update files set IPD_submission_file = '{}' where cell_line = '{}'
                    """.format(subm_file, cell_line)
                    update_queries.append(update_files_query)
                    
                    # update samples table with customer:
                    update_samples_query = """update samples set customer = '{}' where sample_id_int = '{}'
                    """.format(self.customer_dic[sample], sample)
                    update_queries.append(update_samples_query)
                    
                    # copy file to sample folder:
                    src_path = os.path.join(os.path.dirname(self.IPD_file), subm_file)
                    dest_dir = os.path.join(self.settings["projects_dir"], self.project, sample)
                    if not os.path.isdir(dest_dir):
                        self.log.warning("Sample folder {} does not exist! Creating...".format(dest_dir))
                        QMessageBox.warning(self, "Sample path unknown", """Sample directory '{}' does not exist (but it should)!
                        I'm creating it, but please notify your admin!""".format(dest_dir))
                        os.makedirs(dest_dir)
                    dest_path = os.path.join(dest_dir, subm_file)
                    self.log.debug("Copying IPD file to {}...".format(dest_path))
                    try:
                        shutil.copy(src_path, dest_path)
                    except Exception as E:
                        self.log.warning("Could not copy file {} to {}".format(subm_file, dest_dir))
                        self.log.exception(E)
                        QMessageBox.warning(self, "File copy error", "Could not copy file '{}' to its sample-folder '{}'!".format(os.path.basename(subm_file), dest_dir))
                    
                # update IPD_submissions table:
                today = time.strftime("%Y-%m-%d")
                query2 = """insert into IPD_submissions 
                (SUBMISSION_ID, NR_ALLELES, TIMESTAMP_SENT, SUCCESS) values
                ('{}', {}, '{}', 'yes')""".format(self.subm_id, len(self.cell_lines), today)
                update_queries.append(query2)
                
                success = db_internal.execute_transaction(update_queries, self.mydb, self.log, 
                                                  "trying to save this submission to the database", 
                                                  "Database error", self)
                if success:
                    self.IPD_submitted.emit()
                    self.log.info("=> Database updated successfully")
                
                else:
                    self.log.info("=> Database NOT updated!")
            except Exception as E:
                QMessageBox.warning(self, "Database error", 
                                    "Could not save this IPD submission to the database (see below). Rolling back...\n\n{}".format(repr(E)))
                self.log.error(E)
                self.log.exception(E)
            
    def define_section4(self):
        """defining section 4: download IPD file
        """
        mywidget = QWidget(self)
        layout = QGridLayout()
        mywidget.setLayout(layout)
        
        self.textbox = QTextEdit(self)
        self.textbox.setMinimumHeight(200)
        
        layout.addWidget(self.textbox, 0, 0, 2, 1)
        
        self.download_btn = QPushButton("Download zipped IPD files", self)
        self.download_btn.setEnabled(False)
        self.download_btn.clicked.connect(self.download_IPD_file)
        layout.addWidget(self.download_btn, 0, 1)
        
        self.ok_btn = QPushButton("Close", self)
        self.ok_btn.setEnabled(False)
        self.ok_btn.clicked.connect(self.close)
        layout.addWidget(self.ok_btn, 1, 1)
        
        self.sections.append(("(4) Check results:", mywidget))

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
    print(settings_dic["modus"])
    mydb = create_connection(log, settings_dic["db_file"])
    
    project = "20180716_ADMIN_KIR3DP1_PB4"
    app = QApplication(sys.argv)
    ex = IPDSubmissionForm(log, mydb, project, settings_dic)
    ex.show()
    
    result = app.exec_()
    close_connection(log, mydb)
    log.info("<End>")
    sys.exit(result)


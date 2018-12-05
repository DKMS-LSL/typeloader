#!/usr/bin/env python3
# -*- coding: cp1252 -*-
'''
Created on 13.03.2018

typeloader_GUI.py

A cross-plattform GUI for Typeloader

@author: Bianca Schoene
'''

# import modules:

import sys, os, ctypes, time, platform
from functools import partial
from datetime import datetime
from PyQt5.QtWidgets import (QMainWindow, QApplication, QDialog, 
                             QMessageBox, QAction, QGridLayout,
                             QLabel, QStackedWidget, 
                             QWidget, QStyleFactory, QSplashScreen)
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5 import QtSql
from PyQt5.QtCore import pyqtSlot, Qt
from configparser import NoSectionError

import general, db_internal
import GUI_navigation, GUI_login, GUI_stylesheet
import GUI_forms_new_project, GUI_forms_new_allele, GUI_forms_new_allele_bulk 
import GUI_forms_submission_ENA, GUI_forms_submission_IPD
import GUI_views_OVprojects, GUI_views_OValleles, GUI_views_project, GUI_views_sample
import GUI_views_settings
import GUI_download_files
from GUI_misc import UnderConstruction
import patches

#===========================================================
# parameters:

from __init__ import __version__
#===========================================================
# classes:

class MainGUI(QMainWindow):
    def __init__(self, db, log, settings_dic):
        super().__init__()
        self.log = log
        self.mydb = db
        self.settings = settings_dic
        self.current_project = ""
        self.current_sample = ""
        self.uncommitted_changes = False
        self.initUI()
    
    def initUI(self):               
        """establish start GUI
        """
        self.log.debug("Establishing main window...")
        self.resize(1000, 500)
        self.setWindowTitle('TypeLoader')
        self.setWindowIcon(QIcon(general.favicon))
        
        self.statusBar()
        
        self.central_widget = QWidget()    
        self.setCentralWidget(self.central_widget)
        
        self.grid = QGridLayout()
        self.central_widget.setLayout(self.grid)
        self.setLayout(self.grid)
        
        self.make_stack()
        self.make_leftlist()
        self.display(2) # index of initially displayed stack-item
        
        self.add_menu()
        
    def make_leftlist(self):
        """sets up the navigation area
        """
        self.navigation = GUI_navigation.Navigation(self.log, self.settings)
        self.navigation.setMaximumWidth(250)
        self.navigation.setMinimumWidth(200)
        #ToDo: make Navigation width dependent on desktop width
        self.grid.addWidget(self.navigation, 0,0)
        self.navigation.changed_allele.connect(self.change_allele)
        self.navigation.changed_projects.connect(self.change_project)
        self.navigation.change_view.connect(self.display)
        self.navigation.refresh.connect(self.refresh_navigation)
        
    def make_stack(self):
        """prepares stacked widgits (the actual main widgits) 
        to mainGUI
        """
        self.log.debug("Creating stack widgets for main area...")
        self.Stack = QStackedWidget (self)
        self.grid.addWidget(self.Stack, 0,1)
        self.stacked_widgits = {}
        
        self.log.debug("\tCreating stack item 0: Under Construction")
        self.stacked_widgits[0] = "Under Construction"
        mywidget = UnderConstruction(self.log)
        self.view_under_construction = self.make_stack_widget("Under construction", mywidget)
        
        self.log.debug("\tCreating stack item 1: Alleles overview")
        self.stacked_widgits[1] = "Allele Overview"
        mywidget = GUI_views_OValleles.AllelesOverview(self.log, self.mydb)
        self.log.debug("=> Making stack widget...")
        self.view_ov_alleles = self.make_stack_widget("Allele Overview", mywidget)
        self.log.debug("=> Stack item created")
        self.view_ov_alleles.widget.changed_projects.connect(self.change_project)
        self.view_ov_alleles.widget.change_view.connect(self.display)
        self.view_ov_alleles.widget.changed_allele.connect(self.change_allele)
        self.log.debug("\t=> Allele Overview done")
        self.log.debug("\tCreating stack item 2: Project overview")
        self.stacked_widgits[2] = "Project Overview"
        mywidget = GUI_views_OVprojects.ProjectsOverview(self.log, self.mydb, self)
        self.view_ov_projects = self.make_stack_widget("Project Overview", mywidget)
        self.view_ov_projects.widget.changed_projects.connect(self.change_project)
        self.view_ov_projects.widget.change_view.connect(self.display)
        self.view_ov_projects.widget.deleted_project.connect(self.on_projects_changed)
        self.view_ov_projects.widget.submit_to_ENA.connect(self.open_ENA_submission_dialog)
        self.view_ov_projects.widget.submit_to_IPD.connect(self.open_IPD_submission_dialog)
        self.view_ov_projects.widget.open_new_allele_form.connect(self.open_new_allele_dialog)
        
        self.log.debug("\tCreating stack item 3: Project View")
        self.stacked_widgits[3] = "Project View"
        mywidget = GUI_views_project.ProjectView(self.log, self.mydb, self.current_project, self)
        self.view_project = self.make_stack_widget("Project View", mywidget)
        self.view_project.sub_lbl = QLabel(self.current_project, self.view_project)
        self.view_project.layout.addWidget(self.view_project.sub_lbl, 0, 1)
        self.view_project.sub_lbl.setStyleSheet(general.label_style_main)
        self.view_project.widget.alleles.changed_allele.connect(self.change_allele)
        self.view_project.widget.alleles.change_view.connect(self.display)
        self.view_project.widget.data_changed.connect(self.on_data_changed)
        self.view_project.widget.submit_to_ENA.connect(self.open_ENA_submission_dialog)
        self.view_project.widget.submit_to_IPD.connect(self.open_IPD_submission_dialog)
        self.view_project.widget.update_btn.data_changed.connect(self.refresh_navigation)
        
        self.log.debug("\tCreating stack item 4: Sample View")
        self.stacked_widgits[4] = "Sample View"
        mywidget = GUI_views_sample.SampleView(self.log, self.mydb, self.current_sample, self.current_project, self)
        self.view_sample = self.make_stack_widget("Sample View", mywidget)
        self.view_sample.sub_lbl = QLabel(self.current_sample, self.view_sample)
        self.view_sample.layout.addWidget(self.view_sample.sub_lbl, 0, 1)
        self.view_sample.sub_lbl.setStyleSheet(general.label_style_main)
        self.view_sample.layout.addWidget(mywidget.edit_btn, 0, 6)
        self.view_sample.layout.addWidget(mywidget.download_btn, 0, 7)
        self.view_sample.widget.data_changed.connect(self.on_data_changed)
        self.view_sample.widget.allele_updated.connect(self.change_allele)
        self.view_sample.widget.sample_table.updated.connect(self.view_ov_alleles.widget.refresh)
        
    def make_stack_widget(self, lbl_text, mywidget):
        """creates a QWidget displaying one view and its main label,
        and adds it to self.Stack
        """
        myframe = QWidget()
        myframe.layout = QGridLayout()
        myframe.setLayout(myframe.layout)
        
        myframe.widget = mywidget
        myframe.main_lbl = QLabel(lbl_text + ":", self)
        myframe.layout.addWidget(myframe.main_lbl, 0, 0)
        myframe.main_lbl.setStyleSheet(general.label_style_main)
            
        myframe.layout.addWidget(mywidget, 1, 0, 30, 8)
        self.Stack.addWidget(myframe)
        return myframe
    
    def refresh_navigation(self, project = None):
        """re-create the model of the navigation area plus expand and select current project
        """
        self.navigation.create_model()
        if project:
            self.current_project = project
        if self.current_project:
            self.navigation.expand_project(self.current_project)
                
    def change_project(self, project, status = "Open"):
        """changes current project to project 
        and filters ProjectView to it
        """
        if self.uncommitted_changes:
            self.log.warning("Please confirm or discard your changes first!")
        else:
            self.log.debug("Changing project to {}...".format(project))
            self.current_project = project
            self.view_project.widget.filter(project)
            self.view_project.sub_lbl.setText(project)
            self.view_project.widget.refresh()
#             self.refresh_navigation()
        
    def change_allele(self, sample, nr, project):
        """changes current sample to sample 
        and filters SampleView to allele <nr> of sample
        """ 
        if self.uncommitted_changes:
            self.log.warning("Please confirm or discard your changes first!")
        else:
            self.log.debug("Changing allele to {} #{} (project {})...".format(sample, nr, project))
            self.current_sample = sample
            self.current_project = project
            self.view_sample.widget.filter_sample_view(sample, nr, project)
            self.view_sample.sub_lbl.setText(sample)
            self.navigation.select_sample(self.current_project, sample, nr)
            self.view_project.widget.refresh()
        
    def display(self, i):
        """changes the currently displayed Widget of the Stack
        to the ith stack-item
        """
        if self.uncommitted_changes:
            message = "Please commit or discard your changes first!"
            self.log.warning(message)
            QMessageBox.warning(self, "Unsaved changes", message)
        else:
            self.log.info("Displaying View #{}: {}".format(i, self.stacked_widgits[i]))
            self.Stack.setCurrentIndex(i)
            if i == 0:
                sender = self.sender().text()
                self.log.warning("{} does not work, yet!".format(sender))
    
    def add_menu(self):
        """creates menu and toolbar
        """
        self.menubar = self.menuBar()
        self.toolbar = self.addToolBar("Show Toolbar")
        self.toolbar.setMovable(False)
        self.toolbar.setFloatable(False)
        
#         self.file_menu = self.menubar.addMenu('&Main')
        
        # analyse new sequence:
        self.new_menu = self.menubar.addMenu('&New')
        
        new_seq_act = QAction('New &Sequence', self)
        new_seq_act.setShortcut('Ctrl+N')
        new_seq_act.setStatusTip('Upload a sequence from a fasta or XML file')
        new_seq_act.triggered.connect(self.open_new_allele_dialog)
        self.new_menu.addAction(new_seq_act)
        self.toolbar.addAction(new_seq_act)
        
        new_bulk_act = QAction('New Sequences (&Bulk fasta upload)', self)
        new_bulk_act.setShortcut('Ctrl+B')
        new_bulk_act.setStatusTip('Upload multiple sequences in fasta format')
        new_bulk_act.triggered.connect(self.open_new_allele_bulk_dialog)
        self.new_menu.addAction(new_bulk_act)
        
        # start new project:
        new_proj_act = QAction('New &Project', self)
        new_proj_act.setShortcut('Ctrl+P')
        new_proj_act.setStatusTip('Start a new project')
        new_proj_act.triggered.connect(self.open_new_project_dialog)
        self.new_menu.addAction(new_proj_act)
        self.toolbar.addAction(new_proj_act)
        
        # See overviews (ov):
        self.ov_menu = self.menubar.addMenu('&Overviews')
        
        ov_samples_act = QAction('&Allele Overview', self.ov_menu)
        ov_samples_act.setShortcut('Ctrl+Alt+A')
        ov_samples_act.setStatusTip('View an overview of all samples')
        ov_samples_act.triggered.connect(partial(self.display, 1))
        self.ov_menu.addAction(ov_samples_act)
        self.toolbar.addAction(ov_samples_act)
        
        ov_projects_act = QAction('&Project Overview', self.ov_menu)
        ov_projects_act.setShortcut('Ctrl+Alt+P')
        ov_projects_act.setStatusTip('View an overview of all projects')
        ov_projects_act.triggered.connect(partial(self.display, 2))
        self.ov_menu.addAction(ov_projects_act)
        self.toolbar.addAction(ov_projects_act)
        
        # submit stuff:
        self.submit_menu = self.menubar.addMenu('&Submit alleles')
        
        ENA_act = QAction('Submit to &ENA', self.submit_menu)
        ENA_act.setShortcut('Ctrl+E')
        ENA_act.setStatusTip('Submit alleles of a project to ENA')
        ENA_act.triggered.connect(self.open_ENA_submission_dialog)
        self.submit_menu.addAction(ENA_act)
        self.toolbar.addAction(ENA_act)
        
        IPD_act = QAction('Submit to &IPD', self.submit_menu)
        IPD_act.setShortcut('Ctrl+I')
        IPD_act.setStatusTip('Submit alleles of a project to IPD')
        IPD_act.triggered.connect(self.open_IPD_submission_dialog)
        self.submit_menu.addAction(IPD_act)
        self.toolbar.addAction(IPD_act)
        
        # Options:
        self.options_menu = self.menubar.addMenu('O&ptions')
        settings_act = QAction(QIcon(os.path.join('icons', 'settings.png')), "Edit &User Settings", self.options_menu)
        settings_act.setShortcut('Ctrl+U')
        settings_act.triggered.connect(self.open_user_settings_dialog)
        settings_act.setStatusTip('View or edit your TypeLoader settings')
        self.options_menu.addAction(settings_act)
        self.toolbar.addAction(settings_act)
        
        dld_ex_act = QAction("&Download example files", self.options_menu)
        dld_ex_act.setShortcut('Ctrl+D')
        dld_ex_act.triggered.connect(self.open_ExampleFileDialog)
        settings_act.setStatusTip('Download example files')
        self.options_menu.addAction(dld_ex_act)
        
#         # generate status report:
#         report_status_act = QAction('Generate status report', self)
#         report_status_act.setShortcut('Ctrl+R')
#         report_status_act.setStatusTip('Generates a status report file')
#         report_status_act.triggered.connect(partial(self.display, 0)) #TODO: (future) implement report_status_samples_act & connect
#         self.file_menu.addAction(report_status_act)
#         self.toolbar.addAction(report_status_act)
    
    def open_new_project_dialog(self):
        """opens the 'New Project' dialog & connects its signals to the rest-GUI
        """
        dialog = GUI_forms_new_project.NewProjectForm(self.log, self.mydb, self.settings, self)
        dialog.project_changed.connect(self.change_project)
        dialog.refresh_projects.connect(self.on_projects_changed)
    
    def open_new_allele_dialog(self, project = None):
        """opens the 'New Allele' dialog & connects its signals to the rest-GUI
        """
        try:
            if project:
                self.current_project = project
            dialog = GUI_forms_new_allele.NewAlleleForm(self.log, self.mydb, self.current_project, self.settings, self)
            dialog.refresh_alleles.connect(self.on_allele_changed)
        except Exception as E:
            self.log.exception(E)
    
    def open_new_allele_bulk_dialog(self, project = None):
        """opens the 'NewAllele' dialog & connects its signals to the rest-GUI
        """
        try:
            if project:
                self.current_project = project
            dialog = GUI_forms_new_allele_bulk.NewAlleleBulkForm(self.log, self.mydb, self.current_project, self.settings, self)
            dialog.refresh_project.connect(self.refresh_navigation)
        except Exception as E:
            self.log.exception(E)
    
    def open_ENA_submission_dialog(self, project = None):
        """opens the 'ENA submission' dialog & connects it to the rest-GUI
        """
        self.log.debug("Opening ENA Submission dialog...")
        if not project:
            project = self.current_project
        try:
            dialog = GUI_forms_submission_ENA.ENASubmissionForm(self.log, self.mydb, project, self.settings, self)
            dialog.ENA_submitted.connect(self.refresh_navigation)
        except Exception as E:
            self.log.exception(E)
        
    def open_IPD_submission_dialog(self, project = None):
        """opens the 'IPD submission' dialog & connects it to the rest-GUI
        """
        self.log.debug("Opening IPD Submission dialog...")
        try:
            if not project:
                project = self.current_project
            dialog = GUI_forms_submission_IPD.IPDSubmissionForm(self.log, self.mydb, project, self.settings, self)
            dialog.IPD_submitted.connect(self.refresh_navigation)
        except Exception as E:
            self.log.exception(E)
        
    def open_user_settings_dialog(self):
        """opens the 'UserSettings' dialog
        """
        GUI_views_settings.UserSettingsDialog(self.settings, self.log, self)
        
    def open_ExampleFileDialog(self):
        """opens the 'ExampleFiles' dialog
        """
        GUI_download_files.ExampleFileDialog(self.settings, self.log, self)
        
    def on_projects_changed(self):
        """when a new project has been created or a project been deleted,
        update Navigation area & refresh projects overview
        """
        if self.uncommitted_changes:
            self.log.warning("Please confirm or discard your changes first!")
        else:
            self.view_ov_projects.widget.refresh()
            self.refresh_navigation()
        
    def on_allele_changed(self, project, sample):
        """when a new allele has been created 
        update Navigation area & refresh alleles overview
        """
        if self.uncommitted_changes:
            self.log.warning("Please confirm or discard your changes first!")
        else:
            try:
                self.current_project = project
                self.current_sample = sample
                self.view_ov_alleles.widget.refresh()
                self.view_ov_projects.widget.refresh()
                self.view_project.widget.refresh()
                self.refresh_navigation()
                self.navigation.select_sample(project, sample, 1)
            except Exception as E:
                self.log.exception(E)
    
    @pyqtSlot(bool)
    def on_data_changed(self, changes):
        """stores whether there are uncommitted changes in the current view
        """ 
        self.uncommitted_changes = changes
        self.on_allele_changed(self.current_project, self.current_sample)
            
    def closeEvent(self, event):
        """asks for confirmation before closing
        """
        if (self.mydb.open()):
            self.mydb.close()
        
        if self.settings["modus"] == "debugging":
            return
        
        self.log.debug("Asking for confirmation before closing...")
        reply = QMessageBox.question(self, 'Message',
            "Quit Typeloader?", QMessageBox.Yes | 
            QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            self.log.debug("Closing TypeLoader...")
            event.accept()
        else:
            self.log.debug("Not closing TypeLoader.")
            event.ignore()
   
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
    

def create_connection(log, mydb):
    """creates a connection to the SQLite db
    """
    log.debug("Creating db connection...")
    db = QtSql.QSqlDatabase.addDatabase("QSQLITE")
    db.setDatabaseName(mydb)
    if not db.open():
        log.error("Cannot establish a database connection to {}!".format(mydb))
        return False
    log.debug("\t=> Connection open")
    return db


def close_connection(log, mydb):
    """if connection to db is open, closes it
    """
    log.debug("Closing connection to db...")
    if mydb:
        if (mydb.open()):
            mydb.close()
    log.debug("\t=> Connection closed")


def cleanup_recovery(settings_dic, log):
    """deletes recovery files older than x days
    where x = settings_dic["keep_recovery"]
    """ 
    if settings_dic:
        log.info("Cleaning up old recovery files...")
        now = datetime.now()
        recovery_dir = settings_dic["recovery_dir"]
        for filename in os.listdir(recovery_dir):
            timestamp = filename.split("_")[0]
            file_date = datetime.strptime(timestamp, "%Y%m%d")
            tdelta = now - file_date
            if tdelta.days > int(settings_dic["keep_recovery"]):
                log.debug("\tDeleting {}... ({} days old)".format(filename, tdelta.days))
                os.remove(os.path.join(recovery_dir, filename))
        
        # also clean up old general log files:
        general_dir = os.path.join(settings_dic["root_path"], settings_dic["general_dir"])
        for filename in os.listdir(general_dir):
            if filename.endswith(".log"):
                try:
                    timestamp = filename.split("_")[0]
                    file_date = datetime.strptime(timestamp, "%Y%m%d")
                    tdelta = now - file_date
                    if tdelta.days > int(settings_dic["keep_recovery"]):
                        log.debug("\tDeleting {}... ({} days old)".format(filename, tdelta.days))
                        os.remove(os.path.join(general_dir, filename))
                except Exception as E:
                    log.warning("Could not delete old logs...")
                    log.exception(E)
            
            
def remove_lock(settings_dic, log):
    """removes lockfile 
    (call when closing the app)
    """
    if settings_dic:
        log.debug("Removing lock...")
        try:
            lockfile = os.path.join(settings_dic["login_dir"], ".locked")
        except Exception as E:
            log.info("\tCannot find lockfile: {}".format(repr(E)))
        try:
            os.remove(lockfile)
        except Exception as E:
            log.info("\tCannot remove lockfile {}: {}".format(lockfile, repr(E)))
            pass
        log.debug("\t=> done")
    
    
#===========================================================
# main:
        
if __name__ == '__main__':
    if GUI_login.config_files_missing():
        sys.exit(1)
    
    curr_time = time.strftime("%Y%m%d_%H%M%S")
    
    if platform.system() == "Windows":
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(__version__) # use favicon as TaskBar icon in Windows
    
    app = QApplication(sys.argv)
    app.setStyle(QStyleFactory.create("Fusion"))
    app.setStyleSheet(GUI_stylesheet.make_stylesheet())
    
    cf = GUI_login.get_basic_cf()
    try:
        root_path = cf.get("Paths", "root_path")
    except NoSectionError:
        print("{} must contain parameter 'root_path' in section [Paths]!\nAborting...".format(GUI_login.base_config_file))
        sys.exit(1)
    
    GUI_login.check_root_path(root_path)
    mylog = os.path.join(root_path, "_general", "{}.log".format(curr_time))
    log = general.start_log(level="DEBUG", debug_to_file = mylog)
    log.info("<Start>")
    
    sys.excepthook = log_uncaught_exceptions
    
    patchme = patches.check_patching_necessary(log)
    if patchme:
        patches.request_user_input(root_path, app, log)
        patches.execute_patches(root_path, log)
    
    login = GUI_login.LoginForm(log)
    result = None
    mydb = None
    ok = False
    settings_dic = None
    
    if login.exec_() == QDialog.Accepted: # if login successful:
        try:
            splash_pix = QPixmap(os.path.join('icons', 'TypeLoaderSplash.png'))
            splash = QSplashScreen(splash_pix, Qt.WindowStaysOnTopHint)
            splash.showMessage("    Starting V{}...".format(__version__), Qt.AlignBottom, Qt.white)
            splash.show()
            
            user = login.login
            settings_dic = GUI_login.startup(user, curr_time, log)
            db_file = settings_dic["db_file"]
            
            # implement db bugfixes:
            db_internal.cleanup_missing_cell_lines_in_files_table(settings_dic, log) #149
            
            mydb = create_connection(log, db_file) 
    
            ex = MainGUI(mydb, log, settings_dic)
            ex.showMaximized()
            splash.finish(ex)
            GUI_login.check_for_reference_updates(log, settings_dic, ex)
            result = app.exec_()
            cleanup_recovery(settings_dic, log)
            ok = True
             
        except Exception as E:
            log.error(E)
            log.exception(E)
        finally:
            close_connection(log, mydb)
            remove_lock(settings_dic, log)
            
    log.info("<End>")
    if ok:
        try:
            log.removeHandler(log.debug_handler)
            log.debug_handler.close()
            os.remove(mylog)
        except:
            pass
    sys.exit(result)

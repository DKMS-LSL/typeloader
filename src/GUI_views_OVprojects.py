#!/usr/bin/env python3
# -*- coding: cp1252 -*-
'''
Created on ?

GUI_views_OVProjects.py

ProjectsOverview class for Typeloader

@author: Bianca Schoene
'''

from PyQt5.QtSql import QSqlQueryModel, QSqlQuery
from PyQt5.QtWidgets import QHeaderView, QMenu, QApplication, QMessageBox
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot
from PyQt5.Qt import QPushButton

import sys, os, shutil

import general
from db_internal import check_error
from GUI_overviews import FilterableTable
from __init__ import __version__

#===========================================================
# classes:
           
class ProjectsOverview(FilterableTable):
    """a widget to display a complete overview over 
    all projects
    """
    changed_projects = pyqtSignal(str)
    change_view = pyqtSignal(int)
    deleted_project = pyqtSignal()
    submit_to_ENA = pyqtSignal(str)
    submit_to_IPD = pyqtSignal(str)
    open_new_allele_form = pyqtSignal(str)
    
    def __init__(self, log, mydb, parent = None):
        super().__init__(log, mydb)
        if parent:
            self.settings = parent.settings
        else:
            import GUI_login
            self.settings = GUI_login.get_settings("admin", self.log)
        self.enhance_UI()
        self.show_closed = False
        self.filter_closed()
        self.table.resizeColumnsToContents()
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(7, QHeaderView.Stretch)
        self.add_headers()
        self.update_filterbox()
        
    def enhance_UI(self):
        self.toggle_btn = QPushButton(self)
        self.toggle_btn.setText("Show closed projects!")
        self.toggle_btn.setCheckable(True)
        self.show_closed = False
        self.grid.addWidget(self.toggle_btn, 1, 0)
        self.toggle_btn.toggled.connect(self.on_toggleBtn_clicked)

        self.table.customContextMenuRequested.connect(self.open_menu)
    
    def add_headers(self):
        headers = ["Project Name", "Project Status", "Creation Date", "User Name",
                   "Gene", "Pool", "Title", "Description", "Number of Alleles"]
        for (i, column) in enumerate(headers):   
            self.proxy.setHeaderData(i, Qt.Horizontal, column)
    
    def create_model(self):
        """creates the table model
        """
        self.log.debug("Creating the table model...")
        self.model = QSqlQueryModel()
        self.query_open = """
            SELECT projects.project_name, project_status, creation_date, 
                username, projects.gene, pool, title, description,
                count(alleles.local_name) as nr_alleles
            FROM projects
                LEFT OUTER JOIN alleles 
                    ON projects.project_name = alleles.project_name
            WHERE project_status = 'Open'
            GROUP BY projects.project_name, project_status, creation_date, 
                username, projects.gene, pool, title, description
            ORDER BY projects.project_name desc
            """
        self.query_all = """
            SELECT projects.project_name, project_status, creation_date, 
                username, projects.gene, pool, title, description,
                count(alleles.local_name) as nr_alleles
            FROM projects
                LEFT OUTER JOIN alleles 
                    ON projects.project_name = alleles.project_name
            GROUP BY projects.project_name, project_status, creation_date, 
                username, projects.gene, pool, title, description
            ORDER BY projects.project_name desc
            """
        self.q = QSqlQuery()
        self.log.debug("\t=> Done!")
    
    @pyqtSlot()
    def filter_closed(self):
        """filters the table either for only open projects (default)
        or all projects
        """ 
        if self.show_closed:
            self.log.debug("Filtering for all projects...")
            query = self.query_all
        else:
            self.log.debug("Filtering for only open projects...")
            query = self.query_open

        self.q.exec_(query)
        self.check_error(self.q)
        self.model.setQuery(self.q)
        
    def on_toggleBtn_clicked(self, state):
        """when "ShowAll!" button is toggled, reset query 
        to appropriate filter
        """
        self.show_closed = state
        self.filter_closed()
    
    def open_menu(self, pos):
        """provides a context menu
        """
        menu = QMenu()
        new_act = menu.addAction("Add new Target Allele")
        open_act = menu.addAction("Open Project View")
        select_act = menu.addAction("Select as current Project")
        ena_act = menu.addAction("Submit Project to ENA")
        ipd_act = menu.addAction("Submit Project to IPD")
        del_act = menu.addAction("Delete project if empty")
        
        action = menu.exec_(self.table.mapToGlobal(pos))
        if action:
            row = self.table.indexAt(pos).row()
            myindex = self.model.index(row, 0)
            project = self.model.data(myindex)
            
            if action == select_act:
                self.changed_projects.emit(project)
                self.log.debug("ProjectsOverview emitted changed_projects")
            elif action == open_act:
                self.log.debug("ProjectsOverview emitted changed_projects & change_view")
                self.changed_projects.emit(project)
                self.change_view.emit(3)
            elif action == new_act:
                self.open_new_allele_form.emit(project)
            elif action == ena_act:
                self.submit_to_ENA.emit(project)
            elif action == ipd_act:
                self.submit_to_IPD.emit(project)
            elif action == del_act:
                self.delete_project(project, row)
    
    @pyqtSlot(str, int)
    def delete_project(self, project, row):
        """delete a project from the database & file system if it's empty
        """
        self.log.debug("Attempting to delete project '{}' from database...".format(project))
        q = QSqlQuery()
        count_query = "select count(*) from alleles where project_name = '{}'".format(project)
        q.exec_(count_query)
        check_error(q, self.mydb, self.log)
        alleles = 0
        while q.next():
            alleles = q.value(0)
        if alleles == 0:
            delete_query = "delete from projects where project_name = '{}'".format(project)
            q.exec_(delete_query)
            self.log.debug("\t=> Successfully deleted empty project")
            
            self.log.debug("Attempting to delete project '{}' from file system...".format(project))
            project_dir = os.path.join(self.settings["projects_dir"], project)
            try:
                shutil.rmtree(project_dir)
            except Exception as E:
                self.log.debug("=> File deletion did not work:")
                self.log.error(E)
                self.log.exception(E)
            self.log.debug("=> Project '{}' successfully deleted from database and file system".format(project))
            self.deleted_project.emit()
        else:
            msg = "Project contains {} alleles => cannot delete!".format(alleles)
            QMessageBox.warning(self, "Could not delete", msg)
            self.log.debug("\t=> {}".format(msg))
            
            
    def refresh(self):
        """refreshes the table using setQuery 
        => take care, this might lead to performance issues
        """
        self.model.setQuery(self.model.query().lastQuery())
            
            
#===========================================================
# functions:

# def log_uncaught_exceptions(cls, exception, tb):
#     """reimplementation of sys.excepthook;
#     catches uncaught exceptions, logs them and exits the app
#     """
#     import traceback
#     from PyQt5.QtCore import QCoreApplication
#     log.critical('{0}: {1}'.format(cls, exception))
#     log.exception(msg = "Uncaught Exception", exc_info = (cls, exception, tb))
#     #TODO: (future) maybe find a way to display the traceback only once, both in console and logfile?
#     sys.__excepthook__(cls, exception, traceback)
#     QCoreApplication.exit(1)
    
#===========================================================
# main:


def main():
    from typeloader_GUI import create_connection, close_connection
    import GUI_login
    log = general.start_log(level="DEBUG")
    log.info("<Start {} V{}>".format(os.path.basename(__file__), __version__))
    settings_dic = GUI_login.get_settings("admin", log)
    mydb = create_connection(log, settings_dic["db_file"])
    app = QApplication(sys.argv)
#     sys.excepthook = log_uncaught_exceptions
    
    ex = ProjectsOverview(log, mydb)
    ex.show()#Maximized()
    result = app.exec_()
    
    close_connection(log, mydb)
    log.info("<End>")
    sys.exit(result)


if __name__ == '__main__':
    main()

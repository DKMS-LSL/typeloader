#!/usr/bin/env python3
# -*- coding: cp1252 -*-
'''
Created on ?

GUI_views_OVAlleles.py

AllelesOverview class for Typeloader

@author: Bianca Schoene
'''

from PyQt5.QtSql import QSqlQueryModel, QSqlQuery
from PyQt5.QtWidgets import QMenu, QApplication
from PyQt5.QtCore import Qt, pyqtSignal, QPoint, pyqtSlot

import sys, os

import general
from db_internal import alleles_header_dic
from GUI_overviews import FilterableTable

#===========================================================
# classes:

class AllelesOverview(FilterableTable):
    """a widget to display a complete overview over 
    all data of all alleles
    """
    changed_projects = pyqtSignal(str)
    change_view = pyqtSignal(int)
    changed_allele = pyqtSignal(str, int, str)
    
    def __init__(self, log, mydb):
        super().__init__(log, mydb, header_dic = alleles_header_dic, 
                         add_color_proxy=(8,14))
        self.table.customContextMenuRequested.connect(self.open_menu)
#         self.add_headers()
        self.header_fixed = False
        log.debug("Alleles Overview created")
        
    def create_model(self):
        """creates the table model
        """
        self.log.debug("Creating the table model...")
        self.model = QSqlQueryModel()
        q = QSqlQuery()
        query = """SELECT * --alleles.sample_id_int, new_confirmed, long_read_phasing, null_allele 
        FROM alleles 
        LEFT JOIN samples 
         ON alleles.sample_ID_int = samples.sample_ID_int
        LEFT JOIN ena_submissions
         ON ena_submissions.Submission_id = alleles.ena_submission_id
        LEFT JOIN ipd_submissions
         ON ipd_submissions.submission_id = alleles.ipd_submission_id
        ORDER BY alleles.project_name desc, project_nr 
         """
        q.exec_(query)
        self.check_error(q)
        self.model.setQuery(q)
        self.model.setHeaderData(0, Qt.Horizontal, "Sample-ID (int)")
        self.log.debug("\t=> Done!")
        
    def add_headers(self):
        """configure header to be nice and human-friendly
        """
        self.log.debug("\tAdding headers for Alleles Overview...")
        for i in self.header_dic:
            self.proxy.setHeaderData(i, Qt.Horizontal, self.header_dic[i]) #TODO: figure out why this becomes slow when db becomes larger...
#         for i in range(self.proxy.columnCount()):
#             print (i, "\t", self.proxy.headerData(i, Qt.Horizontal, Qt.DisplayRole),
#                    "\t", self.proxy.data(self.proxy.index(5, i), Qt.DisplayRole))
        self.log.debug("\tHiding duplicate columns in Alleles Overview...")
        for i in [46, 49]:
            self.table.setColumnHidden(i, True)
        self.header_fixed = True # this takes long as db grows => only called on demand, and only once per session
        
    @pyqtSlot(QPoint)
    def open_menu(self, pos):
        """provides a context menu
        """
        menu = QMenu()
        open_allele_act = menu.addAction("Open Allele View")
        open_project_act = menu.addAction("Open Project View")
        select_allele_act = menu.addAction("Select as current Allele")
        select_project_act = menu.addAction("Select project as current Project")
        
        action = menu.exec_(self.table.mapToGlobal(pos))
        if action:
            row = self.table.indexAt(pos).row()
            sample = self.proxy.data(self.proxy.index(row, 0))
            allele_nr = self.proxy.data(self.proxy.index(row, 1))
            project = self.proxy.data(self.proxy.index(row, 2))
            
            if action == select_allele_act:
                self.changed_allele.emit(sample, allele_nr, project)
                self.log.debug("AllelesOverview emitted changed_allele to ({} {} ({})".format(sample, allele_nr, project))
            elif action == select_project_act:
                self.changed_projects.emit(project)
                self.log.debug("AllelesOverview emitted changed_projects")
            elif action == open_allele_act:
                self.changed_allele.emit(sample, allele_nr, project)
                self.change_view.emit(4)
                self.log.debug("AllelesOverview emitted changed_allele to ({} {} ({}) & change_view to AlleleView".format(sample, allele_nr, project))
            elif action == open_project_act:
                self.log.debug("AllelesOverview emitted changed_projects & change_view to ProjectView")
                self.changed_projects.emit(project)
                self.change_view.emit(3)
    
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
    log.info("<Start {}>".format(os.path.basename(__file__)))
    settings_dic = GUI_login.get_settings("admin", log)
    mydb = create_connection(log, settings_dic["db_file"])
    app = QApplication(sys.argv)
#     sys.excepthook = log_uncaught_exceptions
    
    ex = AllelesOverview(log, mydb)
    ex.show()#Maximized()
    result = app.exec_()
    
    close_connection(log, mydb)
    log.info("<End>")
    sys.exit(result)


if __name__ == '__main__':
    main()

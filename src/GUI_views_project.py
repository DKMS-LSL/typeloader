#!/usr/bin/python3
# -*- coding: utf-8 -*-

from PyQt5.QtSql import QSqlQueryModel, QSqlTableModel, QSqlQuery
from PyQt5.QtWidgets import (QHeaderView, QGridLayout, QWidget, QMessageBox,
                             QMenu, QApplication, QPushButton,
                             QAbstractItemView)
from PyQt5.QtCore import Qt, pyqtSignal, QPoint, pyqtSlot

import sys, os

import general, GUI_misc
from db_internal import execute_query
from GUI_overviews import (InvertedTable, FilterableTable, SqlQueryModel_filterable,
                           edit_on_manual_submit, EditFilesButton, EditFileDialog,
                           DownloadFilesButton, DownloadFilesDialog)
from __init__ import __version__

#===========================================================
# classes:

class ProjectInfoTable(InvertedTable):
    """a table displaying general info about a Project
    """
    def __init__(self, log, mydb):
        super().__init__(log, mydb)
        self.create_model()
        self.add_headers()
        self.invert_model()
        self.header_lbl.setText("General Information:")
        
    def create_model(self):
        self.model = QSqlTableModel()
        self.model.setTable("projects")
        self.model.select()
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
    
    def add_headers(self):
        self.model.setHeaderData(1, Qt.Horizontal, "Project Status", Qt.DisplayRole)
        self.model.setHeaderData(2, Qt.Horizontal, "Created on", Qt.DisplayRole)
        self.model.setHeaderData(3, Qt.Horizontal, "Created by", Qt.DisplayRole)
        self.model.setHeaderData(4, Qt.Horizontal, "Gene", Qt.DisplayRole)
        self.model.setHeaderData(5, Qt.Horizontal, "Pool", Qt.DisplayRole)
        self.model.setHeaderData(6, Qt.Horizontal, "Title", Qt.DisplayRole)
        self.model.setHeaderData(7, Qt.Horizontal, "Description", Qt.DisplayRole)
        self.model.setHeaderData(8, Qt.Horizontal, "ENA Project ID", Qt.DisplayRole)
        self.model.setHeaderData(9, Qt.Horizontal, "ENA Project Submission ID", Qt.DisplayRole)
        
    def filter(self, project):
        self.model.layoutAboutToBeChanged.emit()
        self.model.setFilter("projects.project_name = '{}'".format(project))
        self.model.layoutChanged.emit()
        self.table.hideRow(0)
        
        
class ProjectStatsTable(InvertedTable):
    """a table displaying stats of a Project
    """
    def __init__(self, log, mydb):
        super().__init__(log, mydb)
        self.create_model()
        self.invert_model()
        self.header_lbl.setText("Statistics:")
        
    def create_model(self):
        query = """
        SELECT projects.project_name, 
          COUNT(*) AS 'Number of alleles',
          SUM(CASE WHEN alleles.allele_status in ('abandoned', 'IPD accepted', 'IPD released', 'original result corrected') THEN 1 ELSE 0 END) AS 'Closed alleles',
          SUM(CASE WHEN alleles.ENA_SUBMISSION_ID != '' THEN 1 ELSE 0 END) AS 'Submitted to ENA',
          SUM(CASE WHEN alleles.IPD_SUBMISSION_ID != '' THEN 1 ELSE 0 END) AS 'Submitted to IPD',
          SUM(CASE WHEN alleles.IPD_ACCEPTION_DATE != '' THEN 1 ELSE 0 END) AS 'Accepted by IPD',
          SUM(CASE WHEN alleles.allele_status = 'abandoned' THEN 1 ELSE 0 END) AS 'Abandoned'
        FROM projects join alleles
          on projects.PROJECT_NAME = alleles.PROJECT_NAME
        group by projects.project_name
        """
        q = QSqlQuery(query)
        self.model = SqlQueryModel_filterable(query, hasGroupBy = True)
        self.model.setQuery(q)
    
    def filter(self, project):
        self.model.layoutAboutToBeChanged.emit()
        self.model.setFilter("projects.project_name = '{}'".format(project))
        self.model.layoutChanged.emit()
        self.table.hideRow(0)
    
    @pyqtSlot()
    def refresh(self):
        """refreshes the table's content
        """
        self.log.debug("\tRefreshing ProjectView's stats table...")
        self.model.setQuery(self.model.query().lastQuery()) 
    

class ProjectAlleles(FilterableTable):
    """a widget to display all alleles of one project,
    with their most important data
    """
    changed_allele = pyqtSignal(str, int, str)
    change_view = pyqtSignal(int)
    
    def __init__(self, log, mydb):
        super().__init__(log, mydb, add_color_proxy = (4,5))
        self.proxy.setFilterKeyColumn(2)
        self.filter_cb.setCurrentIndex(2)
        self.header_lbl.setText("Alleles:")
        self.table.verticalHeader().hide()
        self.table.customContextMenuRequested.connect(self.open_menu)
        self.project = ""
        self.filter(self.project)

    def create_model(self):
        """creates the table model
        """
        self.log.debug("Creating the table model...")
        self.model = QSqlQueryModel()
        q = QSqlQuery()
        query = """SELECT project_name, project_nr, 
          (sample_id_int || ' #' || allele_nr || ' (' || gene || ')'),
          cell_line,
          allele_status, lab_status,
          sample_id_int, allele_nr
        FROM alleles
        order by project_nr 
         """
        q.exec_(query)
        self.check_error(q)
        self.model.setQuery(q)
        
        self.model.setHeaderData(1, Qt.Horizontal, "Nr")
        self.model.setHeaderData(2, Qt.Horizontal, "Target Allele")
        self.model.setHeaderData(3, Qt.Horizontal, "Cell Line")
        self.model.setHeaderData(4, Qt.Horizontal, "Allele Status")
        self.model.setHeaderData(5, Qt.Horizontal, "Lab Status")
        
        self.log.debug("\t=> Done!")
        
    def filter(self, project):
        self.project = project
        self.proxy.layoutAboutToBeChanged.emit()
        self.proxy.setFilterKeyColumn(0)
        self.proxy.setFilterFixedString(project)
        self.proxy.layoutChanged.emit()
        for col in [0, 6, 7]:
            self.table.hideColumn(col)
    
    @pyqtSlot()
    def refresh(self):
        """refreshes the table's content
        """
        self.log.debug("\tRefreshing ProjectView's allele list...")
        self.model.setQuery(self.model.query().lastQuery())
        
    @pyqtSlot(QPoint)
    def open_menu(self, pos):
        """provides a context menu
        """
        try:
            menu = QMenu()
            open_allele_act = menu.addAction("Open Allele View")
            
            action = menu.exec_(self.table.mapToGlobal(pos))
            if action:
                row = self.table.indexAt(pos).row()
                sample = self.proxy.data(self.proxy.index(row, 6))
                allele_nr = int(self.proxy.data(self.proxy.index(row, 7)))
                if action == open_allele_act:
                    self.changed_allele.emit(sample, allele_nr, self.project)
                    self.change_view.emit(4)
                    self.log.debug("ProjectAlleles emitted changed_allele to {} #{} ({}) & change_view to AlleleView".format(sample, allele_nr, self.project))
        except Exception as E:
            self.log.exception(E)


class ToggleProjectStatusButton(QPushButton):
    """toggles a project's status
    """
    data_changed = pyqtSignal(str)
    
    def __init__(self, project = "", parent=None, log = None, mydb = None):
        self.log = log
        self.mydb = mydb
        self.proj_name = project
        self.values = ["Open", "Closed"]
        self.texts = ["Close Project", "Reopen Project"]
        self.curr_value = self.values[0]
        super().__init__(self.texts[0], parent)
        self.setStyleSheet(general.btn_style_normal)
        self.clicked.connect(self.toggle_data)
        
    def toggle_data(self):
        """toggles the data of one cell between 2 defined states
        """
        if self.curr_value == self.values[0]:
            new_ix = 1
        else:
            new_ix = 0
        new_value = self.values[new_ix]
        self.log.info("Changing state of project '{}' to '{}'...".format(self.proj_name, new_value))
        query = "update PROJECTS set project_status = '{}' where project_name = '{}'".format(new_value, self.proj_name)
        success, _ = execute_query(query, 0, self.log, "Updating project status", "Update error", self)
        if success:
            self.curr_value = new_value
            self.setText(self.texts[new_ix])
            self.data_changed.emit(self.proj_name)
            self.log.info("\t=> Success (emitting data_changed = '{}')".format(self.proj_name))
            
    @pyqtSlot(str)
    def catch_project_name(self, proj_name):
        """catches the current project_name
        """
        self.log.debug("ToggleProjectStatusButton caught new project name '{}'".format(proj_name))
        self.proj_name = proj_name
        status_query = "select project_status from projects where project_name = '{}'".format(proj_name)
        success, data = execute_query(status_query, 1, self.log, "Retrieving project status", "Database error", self)
        if success and data:
            try:
                status = data[0][0]
            except IndexError:
                self.log.error("Error: could not read status from {} (type {}, len{})".format(data, type(data), len(data)))
                status = ""
            
            if status != self.curr_value:
                if self.curr_value == "Open":
                    self.setText(self.texts[1])
                    self.curr_value = status
                else:
                    self.setText(self.texts[0])
                    self.curr_value = status


class ProjectView(QWidget):
    """a widget to display a complete overview over 
    all data of one project
    """
    data_changed = pyqtSignal(bool)
    submit_to_ENA = pyqtSignal(str)
    submit_to_IPD = pyqtSignal(str)
    project_changed = pyqtSignal(str)
    
    def __init__(self, log, mydb, project_name, parent = None):
        """instanciate ProjectView
        """
        super().__init__()
        self.log = log
        self.mydb = mydb
        self.project_name = project_name
        if parent:
            self.settings = parent.settings
        else:
            import GUI_login
            self.settings = GUI_login.get_settings("admin", self.log)
        self.init_UI()
        self.uncommitted_changes = False
        self.filter(project_name)
        
    def init_UI(self):
        """create the layout
        """
        self.grid = QGridLayout()
        self.setLayout(self.grid)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.open_menu)
        
        self.update_btn = ToggleProjectStatusButton(self.project_name, self, self.log, self.mydb)
        self.project_changed.connect(self.update_btn.catch_project_name)
        self.update_btn.data_changed.connect(self.filter)
        self.grid.addWidget(self.update_btn, 0, 2)
        
        self.download_btn = DownloadFilesButton("Download files", self, self.log)
        self.download_btn.clicked.connect(self.open_download_dialog)
        self.grid.addWidget(self.download_btn, 0, 3)
         
        self.edit_btn = EditFilesButton("Edit a file", self, self.log)
        self.edit_btn.clicked.connect(self.open_edit_dialog)
        self.grid.addWidget(self.edit_btn, 0, 4)
        
        self.project_stats = ProjectStatsTable(self.log, self.mydb)
        self.grid.addWidget(self.project_stats, 0, 0, 2, 1)
        
        self.project_info = ProjectInfoTable(self.log, self.mydb)
        self.grid.addWidget(self.project_info, 2, 0, 2, 1)
        
        self.alleles = ProjectAlleles(self.log, self.mydb)
        self.alleles.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.grid.addWidget(self.alleles, 1, 2, 3, 3)
#         spacer = QSpacerItem(1, 1, QSizePolicy.Ignored, QSizePolicy.MinimumExpanding)
#         self.alleles.grid.addItem(spacer, 15, 0)
        
        # stretch:
        self.grid.setColumnStretch(0, 5)
        self.grid.setColumnStretch(1, 1)
        self.grid.setColumnStretch(2, 3)
        self.grid.setColumnStretch(3, 3)
        self.grid.setColumnStretch(4, 3)
        
        self.grid.setRowStretch(1,2)
        self.grid.setRowStretch(2,1)
        self.grid.setRowStretch(3,2)
        self.grid.setRowStretch(4,0)
        
    @pyqtSlot(str)
    def filter(self, project):
        """filter all displayed views to one project
        """
        if self.uncommitted_changes:
            self.log.warning("Please commit or revert changes first!")
            QMessageBox.warning(self, "Uncommitted changes", "You have uncommitted changes. Please commit or discard them before leaving!")
            return

        else:
            self.project_changed.emit(project)
            self.project_name = project
            self.log.debug("Filtering to {}...".format(project))
            self.project_stats.filter(project)
            self.alleles.filter(project)
    #         self.alleles.table.setMaximumHeight(self.alleles.table.verticalHeader().length() + self.alleles.table.horizontalHeader().height() + 5)
            self.project_info.filter(project)
        
    @pyqtSlot(bool)
    def on_data_changed(self, changes):
        """emit TRUE when data in any of the editable tables is changed,
        emit FALSE when changes are confirmed or discarded
        """
        self.uncommitted_changes = changes
        self.data_changed.emit(changes)
        if changes:
            self.log.debug("Data in ProjectView was changed!")
            
    @pyqtSlot(QPoint)
    def open_menu(self, pos):
        """provides a context menu
        """
        self.log.debug("Opening context menu...")
        menu = QMenu()
        submit_ENA_act = menu.addAction("Submit to ENA")
        submit_IPD_act = menu.addAction("Submit to IPD")
        action = menu.exec_(self.mapToGlobal(pos))
        if action:
            if action == submit_ENA_act:
                self.submit_to_ENA.emit(self.project_name)
                self.log.debug("ProjectView emitted 'submit {} to ENA'".format(self.project_name))
            elif action == submit_IPD_act:
                self.submit_to_IPD.emit(self.project_name) 
                self.log.debug("ProjectView emitted 'submit {} to IPD'".format(self.project_name))
    
    @pyqtSlot()
    def open_download_dialog(self):
        """opens DownloadFilesDialog
        """
        self.log.debug("Opening file download dialog...")
        try:
            dialog = DownloadFilesDialog(self.log, self.project_name, parent = self)
            dialog.exec_()
        except Exception as E:
            self.log.exception(E)
            
    @pyqtSlot()
    def open_edit_dialog(self):
        """opens EditFileDialog
        """
        self.log.debug("Opening file editing dialog...")
        try:
            dialog = EditFileDialog(self.log, self.project_name, parent = self)
            dialog.exec_()
        except Exception as E:
            self.log.exception(E)
            
    def refresh(self):
        self.log.debug("Refreshing ProjectView...")
        self.project_stats.refresh()
        self.alleles.refresh()
        
            
           
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
    
    project_name = "20180719_ADMIN_KIR2DS1_NEB1"
    ex = ProjectView(log, mydb, project_name)
    ex.show()#Maximized()
    result = app.exec_()
    
    close_connection(log, mydb)
    log.info("<End>")
    sys.exit(result)


if __name__ == '__main__':
    main()
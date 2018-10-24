#!/usr/bin/python3
# -*- coding: utf-8 -*-

from PyQt5.QtSql import QSqlQuery, QSqlRelation
from PyQt5.QtWidgets import (QHeaderView, QTabWidget, QGridLayout,
                             QWidget, QMessageBox,
                             QLabel, QApplication, QMenu,
                             QFormLayout, QPushButton, QLineEdit)
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot, QPoint
from PyQt5.Qt import QDialog
from PyQt5.QtGui import QIcon

import sys, os

import general, GUI_misc, db_internal
from db_internal import alleles_header_dic
from GUI_overviews import (InvertedTable, FilterableTable, edit_on_manual_submit,
                           SqlQueryModel_filterable, SqlQueryModel_editable,
                           SqlTableModel_protected, 
                           TabTableSimple, TabTableRelational, ComboDelegate,
                           EditFilesButton, DownloadFilesButton,
                           EditFileDialog, DownloadFilesDialog)
from __init__ import __version__

#===========================================================
# classes:

class ChangeExtIdDialog(QDialog):
    """allow the user to change the external sample ID of a sample
    through a popup dialog
    """
    updated = pyqtSignal()
    
    def __init__(self, log, sample_id_int, sample_id_ext, parent = None):
        super().__init__()
        self.log = log
        self.sample_id_ext = sample_id_ext
        self.sample_id_int = sample_id_int
        self.init_UI()
        self.setWindowIcon(QIcon(general.favicon))
        
    def init_UI(self):
        self.log.debug("Opening ChangeExtIdDialog...")
        layout = QFormLayout()
        self.setLayout(layout)
        self.title = "Change a sample's external sample ID"
        
        self.sample_ext_field = QLineEdit(self)
        self.sample_ext_field.setText(self.sample_id_ext)
        layout.addRow(QLabel("New External Sample-ID:"), self.sample_ext_field)
        
        self.ok_btn = QPushButton("Save", self)
        layout.addRow(self.ok_btn)
        self.ok_btn.clicked.connect(self.on_clicked)
            
    def on_clicked(self):
        """when ok_btn is clicked, get content of fields and emit it
        """
        self.log.debug("Asking for confirmation...")
        self.sample_id_ext_new = self.sample_ext_field.text().strip()
        msg = "Are you really sure you want to change the external sample ID "
        msg += "of {} from {} to {}?".format(self.sample_id_int, self.sample_id_ext, self.sample_id_ext_new)
        reply = QMessageBox.question(self, 'Confirm change of external sample ID', msg, QMessageBox.Yes | 
            QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            query = """Update SAMPLES set sample_id_ext = '{}' where sample_id_ext = '{}' and 
            sample_id_int = '{}'""".format(self.sample_id_ext_new, self.sample_id_ext, self.sample_id_int)
            success, _ = db_internal.execute_query(query, 0, self.log, "Updating table SAMPLES", 
                                      "Updating the external sample ID", self)
            
            if success:
                self.log.info("""Changed external sample ID of sample {} from {} to {}
                            """.format(self.sample_id_int, self.sample_id_ext, self.sample_id_ext_new))
                self.log.debug("Emitting signal 'updated'")
                self.updated.emit()
                self.close()

        
class SampleTable(InvertedTable):
    """shows general info of one sample
    """
    updated = pyqtSignal()
    
    def __init__(self, log, mydb):
        super().__init__(log, mydb)
        self.create_model()
        self.invert_model()
        self.header_lbl.setText("General Information:")
        self.model.setHeaderData(0, Qt.Horizontal, "Internal Donor-ID")
        self.model.setHeaderData(1, Qt.Horizontal, "External Donor-ID")
        self.model.setHeaderData(2, Qt.Horizontal, "Customer")
        self.setMaximumHeight(170)
        self.setMaximumWidth(300)
        v_header = self.table.verticalHeader()
        v_header.setFixedWidth(110)
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.open_menu)
        
    def create_model(self):
#         query_text = "select * from samples"
#         editables = {2 : ("update samples SET customer = '{}' where sample_id_int = '{}'", [0])} 
#         self.model = SqlQueryModel_editable(editables, query_text, hasGroupBy = False)
        self.model = SqlTableModel_protected([0, 1])
        self.model.setTable("samples")
        self.model.select()
        self.model.setEditStrategy(edit_on_manual_submit)
        self.table.setModel(self.model)
        
    def filter_sample_table(self, sample_id_int):
        self.model.layoutAboutToBeChanged.emit()
        self.model.setFilter("Sample_ID_int = '{}'".format(sample_id_int))
        self.model.layoutChanged.emit()

    @pyqtSlot(QPoint)
    def open_menu(self, pos):
        """provides a context menu
        """
        self.log.debug("Opening context menu of SampleTable...")
        try:
            menu = QMenu()
            change_ext_act = menu.addAction("Change External Donor-ID")
            
            action = menu.exec_(self.table.mapToGlobal(pos))
            if action:
                if action == change_ext_act:
                    self.sample_id_int = self.model.data(self.model.index(0, 0))
                    sample_id_ext = self.model.data(self.model.index(0, 1))
                    self.qbox = ChangeExtIdDialog(self.log, self.sample_id_int, sample_id_ext, self)
                    self.qbox.updated.connect(self.updated.emit)
                    self.qbox.updated.connect(self.refilter)
                    self.qbox.exec_()
                    
        except Exception as E:
            self.log.exception(E)
            
    def refilter(self):
        """refilters SampleTable after external sample ID was changed
        """
        self.log.debug("Refiltering SampleTable...")
        self.filter_sample_table(self.sample_id_int)
        


class SampleAlleles(FilterableTable):
    """a widget to display all alleles of one sample,
    with their status data
    """
    allele_changed = pyqtSignal(str, int, str)
    
    def __init__(self, log, mydb):
        super().__init__(log, mydb, (4,5))
        self.enhance_UI()
        
        self.proxy.setFilterKeyColumn(2)
        self.filter_cb.setCurrentIndex(2)
        self.table.clicked.connect(self.on_clicked)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
    def enhance_UI(self):
        self.header_lbl.setText("Alleles:")
        self.table.verticalHeader().hide()
        self.setMaximumHeight(170)

    def create_model(self):
        """creates the table model
        """
        self.log.debug("Creating the table model...")
        q = QSqlQuery()
        query = """SELECT sample_id_int, allele_nr, 
            ('#' || allele_nr || ' (' || gene || ')') as Target_allele, cell_line,
            Allele_Status, Lab_Status, project_name
        FROM alleles
         """
        q.exec_(query)
        self.check_error(q)
        self.model = SqlQueryModel_filterable(query)
        self.model.setQuery(q)
        
        self.model.setHeaderData(2, Qt.Horizontal, "Target Allele")
        self.model.setHeaderData(3, Qt.Horizontal, "Cell Line")
        self.model.setHeaderData(4, Qt.Horizontal, "Allele Status")
        self.model.setHeaderData(5, Qt.Horizontal, "Lab Status")
        self.model.setHeaderData(6, Qt.Horizontal, "Project")
        
        self.log.debug("\t=> Done!")

    def on_clicked(self, index):
        sample_index = self.model.index(index.row(), 0)
        sample = self.model.data(sample_index)
        nr_index = self.model.index(index.row(), 1)
        nr = self.model.data(nr_index)
        project = self.model.data(self.model.index(index.row(), 6))
        self.log.debug("SampleAlleles emits 'allele_changed' = ('{}', {}, '{}')".format(sample, nr, project))
        self.allele_changed.emit(sample, nr, project)

    def filter(self, sample_id_int, project):
        self.log.debug("Filtering SampleAlleles for sample '{}'...".format(sample_id_int))
        self.model.layoutAboutToBeChanged.emit()
        self.model.setFilter("sample_id_int = '{}'".format(sample_id_int))
        self.model.layoutChanged.emit()
        self.table.hideColumn(0)
        self.table.hideColumn(1)
            

class TabTableSQLmodelEditable(InvertedTable):
    """an inverted table presenting an editable QSqlQueryModel
    """
    def __init__(self, log, db, tab_nr, query, editables = [], headers = [],
                 hidden_rows = [], add_color_proxy = False):
        super().__init__(log, db, add_color_proxy = add_color_proxy)
        self.nr = tab_nr
        self.headers = headers
        self.hidden_rows = hidden_rows
        self.query = query
        self.editables = editables
        self.create_model()
        self.invert_model()
        self.table.clicked.connect(self.table.edit)
        self.add_headers()
        
    def create_model(self):
        """creates the table model
        """
        self.model = SqlQueryModel_editable(self.editables, self.query)
        q = QSqlQuery(self.query)
        self.model.setQuery(q)
        self.table.setModel(self.model)
#         self.model.setEditStrategy(edit_on_manual_submit) # TODO: add edit_on_manual_submit
        
    def add_headers(self):
        """adds headers
        """
        if self.headers:
            for i in self.headers:
                column = self.headers[i]
                self.model.setHeaderData(i, Qt.Horizontal, column, Qt.DisplayRole)
                    
    def print_columns(self):
        """debugging function: prints all headers of self.model
        """
        for i in range(self.model.columnCount()):
            print(i, self.model.headerData(i, Qt.Horizontal, Qt.DisplayRole))


class AlleleView(QTabWidget):
    """a TabWidget to show all data of one target allele
    """
    def __init__(self, log, mydb, parent = None):
        super().__init__()
        if parent:
            self.settings = parent.settings
        else:
            import GUI_login
            self.settings = GUI_login.get_settings("admin", self.log)
        self.log = log
        self.db = mydb
        self.init_UI()

    def init_UI(self):
        """sets up the tabs of the widget
        """
        self.tabs = []
        self.add_tab_general()
        self.add_tab_typing_orig()
        self.add_tab_lab()
        self.add_tab_typing_new()
        self.add_tab_ENA()
        self.add_tab_IPD()
        self.resize(500,500)

        for tab in self.tabs:
            v_header = tab.table.verticalHeader()
            v_header.setFixedWidth(200)
        
    def add_tab_general(self):
        """creates the "general" tab
        """
        #columns: sample_id_int, allele_nr, project_name, nr_in_project, cell_line, local_name, gene, goal, allele_status, lab_status, int. allele name, official allele name
        hidden_rows = list(range(9,14)) + list(range(15, 33)) + list(range(35,46))
        mytab = TabTableSimple(self.log, self.db, 0, "alleles", hidden_rows, protected_columns = [0, 1, 2, 3, 4], headers =alleles_header_dic, add_color_proxy=(8,14))
        mytab.table.setItemDelegateForRow(7, ComboDelegate(self, general.field_options["goal"]))
        mytab.table.setItemDelegateForRow(8, ComboDelegate(self, general.field_options["allele_status"]))
        mytab.table.setItemDelegateForRow(14, ComboDelegate(self, general.field_options["lab_status"]))
        self.addTab(mytab, "General")
        self.tabs.append(mytab)
            
    def add_tab_typing_orig(self):
        """creates the "original genotyping" tab
        """
        #columns: allele1, allele2, software, version, date
        hidden_rows = list(range(9)) + list(range(14, 46))
        mytab = TabTableSimple(self.log, self.db, 0, "alleles", hidden_rows, headers=alleles_header_dic)
        self.addTab(mytab, "Original Genotyping")
        if self.settings["xml_center_name"] == "DKMS LIFE SCIENCE LAB":
            mytab.table.setItemDelegateForRow(11, ComboDelegate(self, general.field_options["software_old"]))
        
        self.tabs.append(mytab)
        
    def add_tab_lab(self):
        """creates the "lab processing" tab
        """
        #columns: lab_status, panel, pos, SR_data, SR_phasing, SR_tech, LR_data, LR_phasing, LR_tech, comment
        hidden_rows = list(range(14)) + list(range(24,46))
        mytab = TabTableSimple(self.log, self.db, 0, "alleles", hidden_rows, add_color_proxy=(8,14), headers = alleles_header_dic)
        mytab.table.setItemDelegateForRow(14, ComboDelegate(self, general.field_options["lab_status"]))
        mytab.table.setItemDelegateForRow(17, ComboDelegate(self, general.field_options["yesno"])) # Short Read Data
        mytab.table.setItemDelegateForRow(18, ComboDelegate(self, general.field_options["yesno"])) # SR phased
        mytab.table.setItemDelegateForRow(19, ComboDelegate(self, general.field_options["SR tech"], editable=True))
        mytab.table.setItemDelegateForRow(20, ComboDelegate(self, general.field_options["yesno"])) # Long Read Data
        mytab.table.setItemDelegateForRow(21, ComboDelegate(self, general.field_options["yesno"])) # LR phased
        mytab.table.setItemDelegateForRow(22, ComboDelegate(self, general.field_options["LR tech"], editable=True))
        self.addTab(mytab, "Lab Processing")
        self.tabs.append(mytab)
        
    def add_tab_typing_new(self):
        """creates the "New Genotyping" tab
        """
        #columns: goal, target_allele, partner_allele, MM-pos, null_allele, software, version, date, ref_db, db version, int. allele name, off. allele name, new/confirmed
        hidden_rows = list(range(7)) + list(range(8, 24)) + list(range(36, 46))
        mytab = TabTableSimple(self.log, self.db, 0, "alleles", hidden_rows, headers = alleles_header_dic)
        mytab.table.setItemDelegateForRow(7, ComboDelegate(self, general.field_options["goal"]))
        mytab.table.setItemDelegateForRow(27, ComboDelegate(self, general.field_options["yesno"])) # Null allele
        if self.settings["xml_center_name"] == "DKMS LIFE SCIENCE LAB":
            mytab.table.setItemDelegateForRow(28, ComboDelegate(self, general.field_options["software_new"]))
        mytab.table.setItemDelegateForRow(31, ComboDelegate(self, general.field_options["ref_db"]))
        mytab.table.setItemDelegateForRow(35, ComboDelegate(self, general.field_options["new_confirmed"]))
        self.addTab(mytab, "New Genotyping")
        self.tabs.append(mytab)
        
    def add_tab_ENA(self):
        """creates the "ENA Submission" tab
        """
        #columns: ENA_ID_PROJECT, ENA_id_submission, timestamp_sent, timestamp_confirmed, acc_analysis, acc_submission, 
        #         success, ENA_acception_date, ENA_accession_nr
        hidden_rows = list(range(3)) + list(range(4,38)) + list(range(46,56))
        relations = [(2, QSqlRelation("projects", "project_name", "project_name, ena_id_project, ena_id_submission")),
                    (36, QSqlRelation("ena_submissions", "submission_id", 
                                      """submission_id, Timestamp_Sent, timestamp_confirmed, acc_analysis, 
                                         acc_submission, success"""))
                    ]
        header_dic = {3: "ENA Project ID",
                      38 : "ENA Submission ID",
                      39 : "Timestamp sent",
                      40 : "Timestamp confirmed",
                      41 : "Analysis accession nr",
                      42 : "Submission accession nr",
                      43 : "Submission successful?",
                      44 : 'ENA Acception Date',
                      45 : 'ENA Accession Nr'
                      }

        mytab = TabTableRelational(self.log, self.db, 4, "alleles", relations, hidden_rows, 
                                   headers=header_dic, protected_columns = [3, 38, 39, 40, 41, 42, 43, 44, 45])
        #FIXME: column 43 has been made uneditable because the model throws an error when trying to edit (#164)
#         mytab.table.setItemDelegateForRow(43, ComboDelegate(self, general.field_options["yesno"])) # success
        self.addTab(mytab, "ENA Submission")
        self.tabs.append(mytab)
    
    def add_tab_IPD(self):
        """creates the "IPD Submission" tab
        """
        #columns: IPD submission ID, Timestamp data ready, Timestamp confirmed, success, 
        #         IPD Submission Nr, HWS Submission NR, IPD Acception Date, IPD release
        
        header_dic = {39 : 'IPD Submission ID',
                      40 : 'Timestamp Data Ready',
                      41 : 'Timestamp Confirmed',
                      42 : 'Data generated successfully?',
                      43 : 'IPD Submission Nr',
                      44 : 'HWS Submission Nr',
                      45 : 'IPD Acception Date',
                      46 : 'IPD Release'
                      }        
        hidden_rows = list(range(39)) + [47, 48]
        relations = [(39, QSqlRelation("ipd_submissions", "submission_id", "submission_id, Timestamp_sent, timestamp_confirmed, success"))]
        mytab = TabTableRelational(self.log, self.db, 5, "alleles", relations, hidden_rows, 
                                   headers=header_dic, protected_columns = [39, 40, 43, 41, 42])
        #FIXME: columns 41+42 have been made uneditable because the model throws an error when trying to edit (#164) 
        mytab.table.setItemDelegateForRow(42, ComboDelegate(self, general.field_options["yesno"])) # success
        self.addTab(mytab, "IPD Submission")
        self.tabs.append(mytab)

    def filter_allele_view(self, sample, nr, project):
        """filters all tabs to selected allele
        """
        self.log.debug("Filtering to allele #{} of {}...".format(nr, sample))
        for mytab in self.tabs:
            mytab.model.layoutAboutToBeChanged.emit()
            mytab.model.setFilter("alleles.sample_id_int = '{}' and alleles.allele_nr = {} and alleles.project_name = '{}'".format(sample, nr, project))
#             print("header_dic = '{'")
            for i in range(mytab.model.columnCount()):
                if i in mytab.hidden_rows:
                    mytab.table.hideRow(i)
#                 else:
#                     if mytab.nr == 4:
#                         print ("\t{} : '{}',".format(i, mytab.model.headerData(i, Qt.Horizontal, Qt.DisplayRole)))
#             print("\t\t}")
#         

            
class SampleView(QWidget):
    """a widget to display a complete overview over 
    all data of one sample
    """
    data_changed = pyqtSignal(bool)
    allele_updated = pyqtSignal(str, int, str)

    def __init__(self, log, mydb, sample_id_int, project, parent = None):
        """instanciate SampleView
        """
        super().__init__()
        self.log = log
        if parent:
            self.settings = parent.settings
        else:
            import GUI_login
            self.settings = GUI_login.get_settings("admin", self.log)
        self.mydb = mydb
        self.init_UI()
        self.uncommitted_changes = False
        self.filter_sample_view(sample_id_int, 1, project)
        self.project = project
        self.sample_id_int = sample_id_int
        self.nr = None
        self.sample_alleles.allele_changed.connect(self.filter_sample_view)
        
    def init_UI(self):
        """create the layout
        """
        self.grid = QGridLayout()
        self.setLayout(self.grid)
        
        self.edit_btn = EditFilesButton("Edit a file", self, self.log)
        self.edit_btn.clicked.connect(self.open_edit_dialog)
        self.grid.addWidget(self.edit_btn, 0, 2)
        
        self.download_btn = DownloadFilesButton("Download files", self, self.log)
        self.download_btn.clicked.connect(self.open_download_dialog)
        self.grid.addWidget(self.download_btn, 0, 1)
        
        self.sample_table = SampleTable(self.log, self.mydb)
        self.grid.addWidget(self.sample_table, 1, 0)
        
        self.sample_alleles = SampleAlleles(self.log, self.mydb)
        self.sample_alleles.setMinimumHeight(160)
        self.grid.addWidget(self.sample_alleles, 1, 1, 1, 2)
        
        self.allele_view_header = QLabel("", self)
        self.grid.addWidget(self.allele_view_header, 2, 0)
        self.allele_view_header.setStyleSheet(general.label_style_2nd)
        
        self.allele_view = AlleleView(self.log, self.mydb, self)
        self.grid.addWidget(self.allele_view, 3, 0, 10, 2)
        
        widgets = self.allele_view.tabs + [self.sample_table]
        self.confirmReset = GUI_misc.ConfirmResetWidget(widgets, self.log, Qt.Vertical, self, stretch=200)
        self.grid.addWidget(self.confirmReset, 3, 2)
        self.confirmReset.confirm_btn.clicked.connect(self.sample_alleles.model.refresh)
        self.confirmReset.data_changed.connect(self.on_data_changed)
        
        #set stretch:
        for i in range(self.grid.columnCount()-1):
            self.grid.setColumnStretch(i, 3)
        self.grid.setColumnStretch(2, 1)
        
        for i in range(4,9):
            self.grid.setRowStretch(i, 1)
        
    @pyqtSlot(str, int, str)
    def filter_sample_view(self, sample_id_int, nr, project):
        """filter all displayed views to one sample
        """
        if self.uncommitted_changes:
            self.log.warning("Please commit or revert your changes first!")
            QMessageBox.warning(self, "Uncommitted changes", "You have uncommitted changes. Please commit or discard them before leaving!")
            return
        else:
            self.log.debug("Filtering SampleView to {}...".format(sample_id_int))
            self.sample_id_int = sample_id_int
            self.project = project
            self.nr = nr
            self.allele_view_header.setText("Details about Allele #{}:".format(nr))
            self.sample_table.filter_sample_table(sample_id_int)    
            self.allele_view.filter_allele_view(sample_id_int, nr, project)
            if not "SampleAlleles" in str(type(self.sender())): # if signal comes from sample_alleles, don't re-filter it or the selection is lost
                self.sample_alleles.filter(sample_id_int, project)
    
    @pyqtSlot(bool)
    def on_data_changed(self, changes):
        """emit TRUE when data in any of the editable tables is changed,
        emit FALSE when changes are confirmed or discarded
        """
        self.uncommitted_changes = changes
        self.data_changed.emit(changes)
        self.allele_updated.emit(self.sample_id_int, self.nr, self.project)
        if changes:
            self.log.debug("Data in SampleView was changed!")
    
    @pyqtSlot()
    def open_download_dialog(self):
        """opens DownloadFilesDialog
        """
        self.log.debug("Opening file download dialog...")
        try:
            dialog = DownloadFilesDialog(self.log, self.project, self.sample_id_int, self)
            dialog.exec_()
        except Exception as E:
            self.log.exception(E)
            
    @pyqtSlot()
    def open_edit_dialog(self):
        """opens EditFileDialog
        """
        self.log.debug("Opening file editing dialog...")
        try:
            dialog = EditFileDialog(self.log, self.project, self.sample_id_int, self)
            dialog.exec_()
        except Exception as E:
            self.log.exception(E)
        
           
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
    sys.excepthook = log_uncaught_exceptions
    
    project_name = "20180716_ADMIN_KIR3DP1_PB4"
    sample_id_int = "ID908158"
    ex = SampleView(log, mydb, sample_id_int, project_name)
    ex.show()#Maximized()
    result = app.exec_()
    
    close_connection(log, mydb)
    log.info("<End>")
    sys.exit(result)


if __name__ == '__main__':
    main()
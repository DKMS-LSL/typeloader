#!/usr/bin/python3
# -*- coding: utf-8 -*-

from PyQt5.QtSql import QSqlQueryModel, QSqlTableModel, QSqlQuery, QSqlRelationalTableModel
from PyQt5.QtWidgets import (QTableView, QHeaderView, QItemDelegate,
                             QGridLayout, QWidget, QMessageBox,
                             QLabel, QLineEdit, QComboBox, QMenu,
                             QAction, QApplication, QAbstractItemView,
                             QDialog, QFormLayout, QFileDialog,
                             QPlainTextEdit)
from PyQt5.QtCore import (QSignalMapper, QRegExp, Qt, pyqtSlot,
                          QSortFilterProxyModel, QPoint)
from PyQt5.Qt import QPushButton, QIdentityProxyModel
from PyQt5.QtGui import QBrush, QColor, QIcon

import sys, os, shutil

import general, GUI_flipped
from GUI_forms import ChoiceButton, FileButton, ChoiceSection, ProceedButton
from __init__ import __version__

edit_on_manual_submit = QSqlTableModel.OnManualSubmit
#edit_on_manual_submit = QSqlTableModel.OnFieldChange

class SqlQueryModel_filterable(QSqlQueryModel):
    """a subclass of QSqlQueryModel that supports filtering;
    hasGroupBy is a BOOL describing whether the model's query contains a GROUP BY statement
    """
    def __init__(self, query_text, hasGroupBy = False):
        super().__init__()
        self.hasGroupBy = hasGroupBy
        self.query_text = query_text
        
    def setFilter(self, myfilter):
        if self.hasGroupBy:
            filter_word = " HAVING "
        else:
            filter_word = " WHERE "
             
        text = (self.query_text + filter_word + myfilter)
        self.setQuery(text)
        
    def refresh(self):
        self.setQuery(self.query().lastQuery())
        
        
class SqlQueryModel_editable(SqlQueryModel_filterable):
    """a subclass of SqlQueryModel_filterable 
    where individual columns can be defined as editable
    """
    def __init__(self, editables, query_text, hasGroupBy = False):
        """editables should be a dict of format: 
        {INT editable_column_nr : (STR update query to be performed when changes are made on this column
                                   INT model's column number for the filter-column (used in the where-clause),
                                   )} 
        """
        super().__init__(query_text, hasGroupBy)
        self.editables = editables
        
    def flags(self, index):
        fl = QSqlQueryModel.flags(self, index)
        if index.column() in self.editables:
            fl |= Qt.ItemIsEditable
        return fl

    def setData(self, index, value, role=Qt.EditRole):
        if role == Qt.EditRole:
            mycolumn = index.column()
            if mycolumn in self.editables:
                (query, filter_cols) = self.editables[mycolumn]
                values = [value]
                for col in filter_cols:
                    filter_value = self.index(index.row(), col).data()
                    values.append(filter_value)
                q = QSqlQuery(query.format(*values))
                result = q.exec_()
                if result:
                    self.query().exec_()
                else:
                    print(self.query().lastError().text())
                return result
        return QSqlQueryModel.setData(self, index, value, role)

    def setFilter(self, myfilter):
        text = (self.query_text + " WHERE " + myfilter)
        self.setQuery(text)
    
#     def setEditStrategy(self, args):
#         QSqlTableModel.setEditStrategy(args)
        

class SqlTableModel_protected(QSqlTableModel):
    """a subclass of QSqlTableModel 
    where individual columns can be defined as non-editable
    """
    def __init__(self, protected_columns = []):
        """protected_columns should be a list of integers 
         representing the column numbers of all non-editable columns
        """
        super().__init__()
        self.protected = protected_columns
        
    def flags(self, index):
        fl = QSqlTableModel.flags(self, index)
        if index.column() in self.protected:
            fl = Qt.ItemIsEnabled | Qt.ItemIsSelectable # disable Qt.ItemIsEditable
        return fl


class SqlRelationalTableModel_protected(QSqlRelationalTableModel):
    """a subclass of QSqlRelationalTableModel 
    where individual columns can be defined as non-editable
    """
    def __init__(self, protected_columns = []):
        """protected_columns should be a list of integers 
         representing the column numbers of all non-editable columns
        """
        super().__init__()
        self.protected = protected_columns
        
    def flags(self, index):
        fl = QSqlTableModel.flags(self, index)
        if index.column() in self.protected:
            fl = Qt.ItemIsEnabled | Qt.ItemIsSelectable # disable Qt.ItemIsEditable
        return fl

     
class ColorProxyModel(QIdentityProxyModel):
    """a proxy model to change the background color of an allele according to the status;
    bst use underneath the filtering proxy model
    """
    def __init__(self, parent, allele_status_column, lab_status_column):
        super().__init__(parent)
        self.allele_status_column = allele_status_column
        self.lab_status_column = lab_status_column
    
    def data(self, item, role):
        if role == Qt.BackgroundRole:
            if item.column() == self.allele_status_column:
                allele_status = QIdentityProxyModel.data(self, self.index(item.row(), item.column()), Qt.DisplayRole).lower()
                allele_color = general.color_dic[general.allele_status_dic[allele_status]]
                return QBrush(QColor(allele_color))
            elif item.column() == self.lab_status_column:
                lab_status = QIdentityProxyModel.data(self, self.index(item.row(), item.column()), Qt.DisplayRole).lower()
                lab_color = general.color_dic[general.lab_status_dic[lab_status]]
                return QBrush(QColor(lab_color))
        return QIdentityProxyModel.data(self, item, role)
    

class ComboDelegate(QItemDelegate):
    """
    A delegate that places a fully functioning QComboBox in every
    cell of the column to which it's applied
    
    source: https://gist.github.com/Riateche/5984815
    """
    def __init__(self, parent, items, editable = False):
        self.items = items
        self.editable = editable
        QItemDelegate.__init__(self, parent)
        
    def createEditor(self, parent, option, index):
        combo = QComboBox(parent)
        li = []
        for item in self.items:
            li.append(item)
        combo.addItems(li)
        combo.currentIndexChanged.connect(self.currentIndexChanged)
        if self.editable:
            combo.setEditable(True)
        return combo
        
    def setEditorData(self, editor, index):
        editor.blockSignals(True)
        text = index.model().data(index, Qt.DisplayRole)
        try:
            i = self.items.index(text)
        except ValueError:
            i = 0
        editor.setCurrentIndex(i)
        editor.blockSignals(False)
        
    def setModelData(self, editor, model, index):
        model.setData(index, editor.currentText())
        
    @pyqtSlot()
    def currentIndexChanged(self):
        self.commitData.emit(self.sender())
               
               
class SQLTable(QWidget):
    """a basic class to display data from an SQLite database;
    subclass for individual kinds of tables;
    to use, create_model() and fill_UI() have to be reimplmented 
    """
    def __init__(self, log, mydb):
        super().__init__()
        self.log = log
        self.mydb = mydb
        
        self.init_UI()
        self.log.debug("Table initiated!")

    def init_UI(self):
        """initiates a grid for the UI
        """
        self.log.debug("Setting up the table UI...")
        self.grid = QGridLayout()
        self.setLayout(self.grid)
        self.header_lbl = QLabel("", self)
        self.header_lbl.setStyleSheet(general.label_style_2nd)
        self.grid.addWidget(self.header_lbl, 0,0)
        
    def check_error(self, q):
        """call after every q.exec_ to check for errors
        """
        lasterr = q.lastError()
        if lasterr.isValid():
            print(lasterr.text())
            self.mydb.close()
            exit(1)


class FilterableTable(SQLTable):
    """a filterable Table Widget that displays content of an SQLite table;
    for individual widgets, subclass 
     and overwrite the create_model method;
    add_color_proxy should be an (INT allele_status-column, INT lab_status-column) tuple
    """
    def __init__(self, log, mydb = ": memory :", add_color_proxy = False, header_dic = None):
        super().__init__(log, mydb)
        self.add_color_proxy = add_color_proxy
        self.header_dic = header_dic
        self.create_model()
        self.fill_UI()
        self.create_filter_model()
        self.update_filterbox()
        
    def fill_UI(self):
        """sets up the layout
        """
        self.log.debug("\t- Setting up the table...")
        self.table = QTableView()
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.header = self.table.horizontalHeader() # table header
        self.header.setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setAlternatingRowColors(True)
#         self.header.sectionClicked.connect(self.on_header_sectionClicked)
        
        mode = QAbstractItemView.SingleSelection
        self.table.setSelectionMode(mode)
        
        self.grid.addWidget(self.table, 2, 0, 10, 10)

        self.filter_lbl = QLabel("Filter:", self)
        self.grid.addWidget(self.filter_lbl, 1, 2)
        
        self.filter_entry = QLineEdit(self)
        self.grid.addWidget(self.filter_entry, 1, 3)
        self.filter_entry.textChanged.connect(self.on_filter_entry_textChanged)
        self.filter_text = ""
        
        self.filter_cb = QComboBox(self)
        self.grid.addWidget(self.filter_cb, 1, 4)
        self.filter_cb.currentIndexChanged.connect(self.on_filter_cb_IndexChanged)
        
        self.filter_btn = QPushButton("Filter!", self)
        self.grid.addWidget(self.filter_btn, 1, 5)
        self.filter_btn.clicked.connect(self.on_filter_btn_clicked)
        
        self.unfilter_btn = QPushButton("Remove Filter", self)
        self.grid.addWidget(self.unfilter_btn, 1, 6)
        self.unfilter_btn.clicked.connect(self.on_actionAll_triggered)
        
        self.log.debug("\t=> Done!")
    
    def update_filterbox(self):
        """fills the filter-combobox with the header values 
        after the model has been created and set
        """
        column_num = self.model.columnCount()
        if self.header_dic:
            columns = [self.header_dic[i] for i in self.header_dic]
        else:
            columns = [self.proxy.headerData(i, Qt.Horizontal) for i in range(column_num)]
        self.filter_cb.addItems(columns)

    def create_filter_model(self):
        """creates the filter-proxy-model on top of self.model
        """
        self.log.debug("Creating filter model...")
        self.proxy = QSortFilterProxyModel(self)
        if self.add_color_proxy:
            (allele_status_column, lab_status_column) = self.add_color_proxy
            self.log.debug("adding color filter to columns {} and {}".format(allele_status_column, lab_status_column))
            self.color_proxy = ColorProxyModel(self, allele_status_column, lab_status_column)
            self.color_proxy.setSourceModel(self.model)
            self.proxy.setSourceModel(self.color_proxy)
        else:
            self.proxy.setSourceModel(self.model)
        self.table.setSortingEnabled(True)
        self.table.setModel(self.proxy)
        
    def on_filter_cb_IndexChanged(self, index):
        """restricts RegEx filter to selected column
        """
        self.log.debug("Combobox: colum {} selected".format(index))
        self.proxy.setFilterKeyColumn(index)
    
    def on_filter_entry_textChanged(self, text):
        """stores content of filter_entry as self.text 
        """
        self.log.debug("filter text: '{}'".format(text))
        self.filter_text = text
    
    def on_filter_btn_clicked(self):
        """activates RegEx filter to current content of filter_entry and filter_cb
        """
        column = self.filter_cb.currentIndex()
        self.log.debug("Filtering column {} for '{}'".format(column, self.filter_text))
        self.proxy.setFilterKeyColumn(column)
        search = QRegExp(self.filter_text, Qt.CaseInsensitive, QRegExp.RegExp)
        self.proxy.setFilterRegExp(search)
    
    def on_header_sectionClicked(self, logicalIndex):
        """opens a dialog to choose between all unique values for this column,
        or revert to 'All'
        """
        self.log.debug("Header clicked: column {}".format(logicalIndex))
        self.logicalIndex = logicalIndex
        menuValues = QMenu(self)
        self.signalMapper = QSignalMapper(self)  
  
        self.filter_cb.setCurrentIndex(self.logicalIndex)
        self.filter_cb.blockSignals(True)
        self.proxy.setFilterKeyColumn(self.logicalIndex)
        
        valuesUnique = [str(self.model.index(row, self.logicalIndex).data())
                        for row in range(self.model.rowCount())
                        ]
        
        actionAll = QAction("All", self)
        actionAll.triggered.connect(self.on_actionAll_triggered)
        menuValues.addAction(actionAll)
        menuValues.addSeparator()
        
        for actionNumber, actionName in enumerate(sorted(list(set(valuesUnique)))):              
            action = QAction(actionName, self)
            self.signalMapper.setMapping(action, actionNumber)  
            action.triggered.connect(self.signalMapper.map)  
            menuValues.addAction(action)
  
        self.signalMapper.mapped.connect(self.on_signalMapper_mapped)  
  
        headerPos = self.table.mapToGlobal(self.header.pos())        
        posY = headerPos.y() + self.header.height()
        posX = headerPos.x() + self.header.sectionViewportPosition(self.logicalIndex)
  
        menuValues.exec_(QPoint(posX, posY))
      
    def on_actionAll_triggered(self):
        """reverts table to unfiltered state
        """
        self.log.debug("Unfiltering...")
        filterString = QRegExp("", Qt.CaseInsensitive, QRegExp.RegExp)
        self.proxy.setFilterRegExp(filterString)
        self.filter_entry.setText("")
  
    def on_signalMapper_mapped(self, i):
        """filters current column to mapping text
        """
        text = self.signalMapper.mapping(i).text()
        self.log.debug("Filtering column {} to '{}'".format(self.logicalIndex, text))
        filterString = QRegExp(text, Qt.CaseSensitive, QRegExp.FixedString)
        self.proxy.setFilterRegExp(filterString)
        

class InvertedTable(SQLTable):
    """a Widget that displays content of an SQLite query inverted
    (= with rows and columns flipped);
    """
    def __init__(self, log, mydb = ": memory :", add_color_proxy = False):
        self.add_color_proxy = add_color_proxy
        super().__init__(log, mydb)
        self.fill_UI()
        
    def fill_UI(self):
        """sets up the layout
        """
        self.table = QTableView()
        header = self.table.horizontalHeader()
        header.hide()
        header.setStretchLastSection(True)
        self.table.resizeColumnsToContents()
        self.table.setAlternatingRowColors(True)
        self.grid.addWidget(self.table, 1, 0)
        self.log.debug("\t=> Table created!")
    
    def invert_model(self):
        """inverts the model for the table
        """
        self.flipped_model = GUI_flipped.FlippedProxyModel()
        if self.model:
            self.log.debug("Creating the flipped model...")
            if self.add_color_proxy:
                (allele_status_column, lab_status_column) = self.add_color_proxy
                self.log.debug("adding status color background to columns {} and {}".format(allele_status_column, lab_status_column))
                self.color_proxy = ColorProxyModel(self, allele_status_column, lab_status_column)
                self.color_proxy.setSourceModel(self.model)
                self.flipped_model.setSourceModel(self.color_proxy)
            else:
                self.flipped_model.setSourceModel(self.model)
            self.table.setModel(self.flipped_model)
            self.table.setItemDelegate(GUI_flipped.FlippedProxyDelegate(self.table)) # use flipped proxy delegate
            self.log.debug("\t=> Model created")


class TabTableSimple(InvertedTable):
    """an inverted table presenting a QSqlTableModel or QSqlRelationalTableModel()
    """
    def __init__(self, log, db, tab_nr, table, hidden_rows = [], headers = [], protected_columns = [], relational_model = False, add_color_proxy = False):
        super().__init__(log, db, add_color_proxy = add_color_proxy)
        self.nr = tab_nr
        self.headers = headers
        self.table_name = table
        self.hidden_rows = hidden_rows
        self.protected_columns = protected_columns
        self.relational_model = relational_model
        self.create_model(table)
        self.invert_model()
        self.table.clicked.connect(self.table.edit)
        self.add_headers()
        
    def create_model(self, table):
        """creates the table model
        """
        if self.relational_model:
            self.model = QSqlRelationalTableModel()
        else:
            self.model = SqlTableModel_protected(self.protected_columns)
        self.model.setEditStrategy(edit_on_manual_submit)
        self.model.setTable(self.table_name)
        self.model.select()
        
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


class TabTableRelational(InvertedTable):
    """an inverted table presenting a QSqlTableModel or QSqlRelationalTableModel()
    """
    def __init__(self, log, db, tab_nr, table, relations, hidden_rows = [], 
                 headers = {}, relation_headers = {}, protected_columns = [], 
                 add_color_proxy = False):
        super().__init__(log, db, add_color_proxy = add_color_proxy)
        self.nr = tab_nr
        self.headers = headers
        self.table_name = table
        self.relations = relations
        self.relation_headers = relation_headers
        self.hidden_rows = hidden_rows
        self.protected = protected_columns
        self.create_model(table)
        self.add_headers()
        self.invert_model()
        
    def create_model(self, table):
        """creates the table model
        """
        self.model = SqlRelationalTableModel_protected(self.protected)
        self.model.setEditStrategy(edit_on_manual_submit)
        self.model.setTable(self.table_name)
        self.model.select()
        for (column, relation) in self.relations:
            self.model.setRelation(column, relation)
        
    def add_headers(self):
        """adds headers
        """
        if self.headers: # set headers for basis table
            for i in self.headers:
                column = self.headers[i]
                success = self.model.setHeaderData(i, Qt.Horizontal, column, Qt.DisplayRole)
#                 print(i, column, success, self.model.headerData(i, Qt.Horizontal, Qt.DisplayRole))
#         for col in range(self.model.columnCount()):
#             print (col, self.model.headerData(col, Qt.Horizontal, Qt.DisplayRole))
        if self.relation_headers: # set headers for related tables
            for n in self.relation_headers:
                mymodel = self.model.relationModel(n)
#                 for i in range(mymodel.columnCount()):
#                     print(i, mymodel.headerData(i, Qt.Horizontal, Qt.DisplayRole))
                for i in self.relation_headers[n]:
                    column = self.relation_headers[n][i]
#                     print(n, i, column)
                    mymodel.setHeaderData(i, Qt.Horizontal, column, Qt.DisplayRole)
#                 print ("")
                    
    def print_columns(self):
        """debugging function: prints all headers of self.model
        """
        for i in range(self.model.columnCount()):
            print(i, self.model.headerData(i, Qt.Horizontal, Qt.DisplayRole))
            

class EditFilesButton(ChoiceButton):
    """opens an EditFileDialog
    """
    def __init__(self, text = "", parent=None, log = None):
        super().__init__(text, parent)
        self.log = log
        self.setStyleSheet(general.btn_style_normal)


class DownloadFilesButton(ChoiceButton):
    """opens a file dialog to choose files for downloading
    """
    def __init__(self, text = "", parent=None, log = None):
        super().__init__(text, parent)
        self.log = log
        self.setStyleSheet(general.btn_style_normal)
    
    
class DownloadFilesDialog(QDialog):
    """a dialog to choose a file of a sample, and download it to a location of choice
    """
    def __init__(self, log, project, sample_id_int = None, parent = None):
        super().__init__()
        self.log = log
        self.sample = sample_id_int
        self.project = project
        self.file = None
        if parent:
            self.settings = parent.settings
        else:
            import GUI_login
            self.settings = GUI_login.get_settings("admin", log)
        self.setWindowTitle("Download files")
        self.setWindowIcon(QIcon(general.favicon))
        self.resize(300, 150)
        self.init_UI()
        self.show()
        
    def init_UI(self):
        layout = QFormLayout()
        self.setLayout(layout)
        
        lbl_proj = QLabel("Project: {}".format(self.project))
        layout.addRow(lbl_proj)
        if self.sample:
            lbl_sampl = QLabel("Sample: {}".format(self.sample))
            layout.addRow(lbl_sampl)
            self.mydir = os.path.join(self.settings["projects_dir"], self.project, self.sample)
        else:
            self.mydir = os.path.join(self.settings["projects_dir"], self.project)
        choice_btn = FileButton("Choose Files", default_path = self.mydir, parent=self, log = self.log)
        self.file_widget = ChoiceSection("Choose File:", [choice_btn], self)
        self.file_widget.choice.connect(self.get_file)
        layout.addRow(self.file_widget)
        
        self.dld_btn = ProceedButton("Download!", [self.file_widget.field], self.log, parent = self)
        self.dld_btn.clicked.connect(self.download_file)
        self.file_widget.field.textChanged.connect(self.dld_btn.check_ready)
        layout.addRow(self.dld_btn)
        
    def get_file(self, path):
        """catches path from self.file_widget,
        stores it as self.file
        """
        if os.path.dirname(os.path.abspath(path)) == os.path.abspath(self.mydir):
            self.file = path
            self.log.debug("File chosen for download: {}".format(path))
            self.dld_btn.setEnabled(True)
        else: # file not allowed (outside of scope)
            if self.sample:
                category = "does not belong to the sample"
            else:
                category = "is not a project file of the project"
            QMessageBox.warning(self, "Forbidden file", "This file {} you started this dialog from!".format(category))
            self.dld_btn.setEnabled(False)
            self.dld_btn.setStyleSheet(general.btn_style_normal)

    def download_file(self):
        """opens QFileDialog, saves file in chosen location
        """
        if self.file:
            self.log.debug("Downloading file from {}...".format(self.file))
            suggested_path = os.path.join(self.settings["default_saving_dir"], os.path.basename(self.file))
        chosen_path = QFileDialog.getSaveFileName(self, "Download file...", suggested_path)[0]
        if chosen_path:
            shutil.copyfile(self.file, chosen_path)
            self.close()


class EditFileDialog(QDialog):
    """a dialog to choose a file of a sample, view, edit, and save it
    """
    def __init__(self, log, project, sample_id_int = None, parent = None):
        super().__init__()
        self.log = log
        self.sample = sample_id_int
        self.project = project
        self.file = None
        self.txt = ""
        self.unsaved_changes = False
        if parent:
            self.settings = parent.settings
        else:
            import GUI_login
            self.settings = GUI_login.get_settings("admin", log)
        self.setWindowTitle("Edit a file")
        self.setWindowIcon(QIcon(general.favicon))
#         self.resize(800, 800)
        self.init_UI()
        self.show()
        
    def init_UI(self):
        layout = QGridLayout()
        self.setLayout(layout)
        
        lbl_proj = QLabel("Project: {}".format(self.project))
        layout.addWidget(lbl_proj, 0, 0, 1, 2)
        if self.sample:
            lbl_sampl = QLabel("Sample: {}".format(self.sample))
            layout.addWidget(lbl_sampl, 1, 0, 1, 2)
        
        if self.sample:
            self.mydir = os.path.join(self.settings["projects_dir"], self.project, self.sample)
        else:
            self.mydir = os.path.join(self.settings["projects_dir"], self.project)
        choice_btn = FileButton("Choose File", default_path = self.mydir, parent=self, log = self.log)
        self.file_widget = ChoiceSection("Choose File:", [choice_btn], self)
        self.file_widget.choice.connect(self.read_file)
        layout.addWidget(self.file_widget, 2, 0, 2, 2)
        
        self.txt_field = QPlainTextEdit(self)
        self.txt_field.textChanged.connect(self.on_text_changed)
        layout.addWidget(self.txt_field, 4, 0, 5, 2)
        
        self.save_btn = ProceedButton("Save changes!", [self.file_widget.field], self.log, parent = self)
        self.save_btn.clicked.connect(self.save_file)
        layout.addWidget(self.save_btn, 10, 0)
        
        self.discard_btn = ProceedButton("Discard changes!", [self.file_widget.field], self.log, parent = self)
        layout.addWidget(self.discard_btn, 10, 1)
        self.discard_btn.clicked.connect(self.reset_file)
        
        self.close_btn = QPushButton("Close", self)
        self.close_btn.clicked.connect(self.close)
        layout.addWidget(self.close_btn, 11, 0, 1, 2)
        
        for row in range(12):
            if row == 5:
                layout.setRowStretch(row, 1)
            else:
                layout.setRowStretch(row, 0)
        
    def read_file(self, path):
        """catches path from self.file_widget,
        stores it as self.file,
        reads its content and writes it to self.txt_field
        """
        try:
            if os.path.dirname(os.path.abspath(path)) == os.path.abspath(self.mydir):
                self.txt_field.setPlainText("")
                self.file = path
                self.file_widget.field.setText(os.path.basename(path))
                self.log.debug("Opening {}...".format(path))
                with open(self.file, "r") as f:
                    self.txt = f.read()
                self.txt_field.setPlainText(self.txt)
                self.resize(800, 600)
            else:
                if self.sample:
                    category = "does not belong to the sample"
                else:
                    category = "is not a project file of the project"
                QMessageBox.warning(self, "Forbidden file", "This file {} you started this dialog from!".format(category))
        except Exception as E:
            self.log.exception(E)
            QMessageBox.warning(self, "File problem", "An error occurred while trying to read the chosen file:\n\n{}".format(repr(E)))

    def on_text_changed(self):
        """when text in text window is edited, enable & highlight save_btn
        """
        try:
            if self.txt_field.toPlainText() != self.txt:
                self.save_btn.setEnabled(True)
                self.save_btn.setStyleSheet(general.btn_style_clickme)
                self.discard_btn.setEnabled(True)
                self.discard_btn.setStyleSheet(general.btn_style_clickme)
                self.unsaved_changes = True
        except Exception as E:
            self.log.exception(E)

    def save_file(self):
        """saves the edited file
        """
        self.log.debug("'Save changes' was clicked")
        try:
            txt = self.txt_field.toPlainText()
            if txt:
                self.log.debug("Saving changes?")
                reply = QMessageBox.question(self, 'Message',
                                             "Save changes to {}?".format(os.path.basename(self.file)), 
                                             QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
        
                if reply == QMessageBox.Yes:
                    self.log.debug("Saving changes in file {}...".format(self.file))
                    with open(self.file, "w") as g:
                        g.write(txt)
                    self.txt = txt
                    self.unsaved_changes = False
                    self.discard_btn.change_to_normal()
                    self.save_btn.change_to_normal()
                    self.log.debug("=> Success")
                else:
                    self.log.debug("Not saving")
                    self.save_btn.setChecked(False)
                    self.save_btn.setStyleSheet(general.btn_style_clickme)
            else:
                self.log.debug("No text to save...")
        except Exception as E:
            self.log.exception(E)
    
    def reset_file(self):
        """returns the edited file to its previous state
        """
        try:
            self.log.debug("Reversing changes on file {}...".format(self.file))
            self.txt_field.setPlainText(self.txt)
            self.unsaved_changes = False
            self.discard_btn.change_to_normal()
            self.save_btn.change_to_normal()
            self.log.debug("=> Success")
        except Exception as E:
            self.log.exception(E)

    def closeEvent(self, event):
        """asks for confirmation before closing
        """
        if self.unsaved_changes:
            QMessageBox.warning(self, "Unsaved changes", "You have unsaved changes, please save or discard them!")
            self.log.warning("Unsaved changes must be saved or discarded before closing.")
            self.log.debug("Not closing.")
            event.ignore()
        else:
            event.accept()
            
            
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
    
    project_name = "20180706_ADMIN_mixed_bsh"
    sample_id_int = "ID15763275"
    ex = DownloadFilesDialog(log, sample_id_int, project_name)
#     ex = EditFileDialog(log, sample_id_int, project_name)
    ex.show()#Maximized()
    result = app.exec_()
    
    close_connection(log, mydb)
    log.info("<End>")
    sys.exit(result)


if __name__ == '__main__':
    main()
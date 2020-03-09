#!/usr/bin/env python3

from PyQt5.Qt import (QModelIndex, QIdentityProxyModel, QSqlRelationalDelegate)
from PyQt5.QtCore import Qt

class FlippedProxyModel(QIdentityProxyModel):
    """a proxy model where all columns and rows are inverted
     (compared to the source model);
    source: http://www.howtobuildsoftware.com/index.php/how-do/bgJv/pyqt-pyside-qsqltablemodel-qsqldatabase-qsqlrelationaltablemodel-with-qsqlrelationaldelegate-not-working-behind-qabstractproxymodel
    """
    def mapFromSource(self, index):
        return self.createIndex(index.column(), index.row())

    def mapToSource(self, index):
        return self.sourceModel().index(index.column(), index.row(), QModelIndex())

    def columnCount(self, parent=QModelIndex()):
        return self.sourceModel().rowCount(QModelIndex())

    def rowCount(self, parent=QModelIndex()):
        return self.sourceModel().columnCount(QModelIndex())

    def index(self, row, column, parent=QModelIndex()):
        return self.createIndex(row, column)

    def parent(self, index):
        return QModelIndex()

    def data(self, index, role):
        return self.sourceModel().data(self.mapToSource(index), role)

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal:
            return self.sourceModel().headerData(section, Qt.Vertical, role)
        if orientation == Qt.Vertical:
            return self.sourceModel().headerData(section, Qt.Horizontal, role)
    

class FlippedProxyDelegate(QSqlRelationalDelegate):
    """a delegate for handling data displayed through a FlippedProxyModel;
    source: http://www.howtobuildsoftware.com/index.php/how-do/bgJv/pyqt-pyside-qsqltablemodel-qsqldatabase-qsqlrelationaltablemodel-with-qsqlrelationaldelegate-not-working-behind-qabstractproxymodel
    """
    def createEditor(self, parent, option, index):
        proxy = index.model()
        base_index = proxy.mapToSource(index)
        return super(FlippedProxyDelegate, self).createEditor(parent, option, base_index)
    
    def setEditorData(self, editor, index):
        proxy = index.model()
        base_index = proxy.mapToSource(index)
        return super(FlippedProxyDelegate, self).setEditorData(editor, base_index)
    
    def setModelData(self, editor, model, index):
        base_model = model.sourceModel()
        base_index = model.mapToSource(index)
        return super(FlippedProxyDelegate, self).setModelData(editor, base_model, base_index)

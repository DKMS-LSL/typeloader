import sys, os
from PyQt5 import QtSql
from PyQt5.QtWidgets import (QGridLayout, QWidget, QMessageBox,
                             QLabel, QApplication, QMenu)
from PyQt5.QtCore import (Qt, QAbstractItemModel, QObject, QPoint)
from PyQt5.Qt import QModelIndex, QTreeView, pyqtSlot, pyqtSignal, QPixmap,\
    QInputDialog, QLineEdit
from PyQt5.QtGui import QIcon

import general, db_internal
from __init__ import __version__

class Node(QObject):
    """source: https://www.youtube.com/watch?v=1WWp71fTdTQ&index=12&list=PLJewNuO700GfElihmE9R8zManDym4S13m
    """
    def __init__(self, name, parent = None, typeinfo = "NODE", status = None):
        super().__init__()
        self._name = name
        self._typeinfo = typeinfo
        self.status = status
        self._children = []
        self._parent = parent
        
        if parent is not None:
            parent.addChild(self)

    def addChild(self, child):
        self._children.append(child)

    def insertChild(self, position, child):
        if position < 0 or position > len(self._children):
            return False
        
        self._children.insert(position, child)
        child._parent = self
        return True

    def removeChild(self, position):
        if position < 0 or position > len(self._children):
            return False
        
        child = self._children.pop(position)
        child._parent = None
        return True

    def name(self):
#         if self._typeinfo == "Project":
#             return "{} ({})".format(self._name, len(self._children))
        return self._name

    def setName(self, name):
        self._name = name

    def child(self, row):
        return self._children[row]
    
    def childCount(self):
        return len(self._children)

    def parent(self):
        return self._parent
    
    def row(self):
        if self._parent is not None:
            return self._parent._children.index(self)

    def log(self, tabLevel=-1):
        output = ""
        tabLevel += 1
        for i in range(tabLevel):
            output += "\t"
        output += "|------{} ({})\n".format(self._name, self.status)
        for child in self._children:
            output += child.log(tabLevel)
        tabLevel -= 1
        return output

    def __repr__(self):
        return self.log()


class TreeModel(QAbstractItemModel):
    """a hierarchical data model;
    make editable by adding Qt.ItemIsEditable to flags
    
    source: https://www.youtube.com/watch?v=1WWp71fTdTQ&index=12&list=PLJewNuO700GfElihmE9R8zManDym4S13m
    """
    def __init__(self, root, parent=None):
        """INPUTS: Node, QObject"""
        super(TreeModel, self).__init__(parent)
        self._rootNode = root

    def rowCount(self, parent):
        """INPUTS: QModelIndex,
        OUTPUT: int
        """
        if not parent.isValid():
            parentNode = self._rootNode
        else:
            parentNode = parent.internalPointer()

        return parentNode.childCount()

    def columnCount(self, parent):
        """INPUTS: QModelIndex,
        OUTPUT: int"""
        return 1
    
    def data(self, index, role):
        """INPUTS: QModelIndex, int,
        OUTPUT: QVariant, strings are cast to QString which is a QVariant"""
        if not index.isValid():
            return None

        node = index.internalPointer()
        if role == Qt.DisplayRole or role == Qt.EditRole:
            if index.column() == 0:
                return node.name()
            
    def setData(self, index, value, role=Qt.EditRole):
        """INPUTS: QModelIndex, QVariant, int (flag)
        """
        if index.isValid():
            if role == Qt.EditRole:
                node = index.internalPointer()
                node.setName(value)
                return True
        return False
    
    def flags(self, index):
        """INPUTS: QModelIndex,
        OUTPUT: int (flag)"""
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def parent(self, index):
        """Should return the parent of the node with the given QModelIndex,
        INPUTS: QModelIndex,
        OUTPUT: QModelIndex"""
        node = self.getNode(index)
        parentNode = node.parent()
        if parentNode == self._rootNode:
            return QModelIndex()
        return self.createIndex(parentNode.row(), 0, parentNode)
        
    def index(self, row, column, parent):
        """Should return a QModelIndex that corresponds to the given row, column and parent node
        INPUTS: int, int, QModelIndex,
        OUTPUT: QModelIndex"""
        parentNode = self.getNode(parent)
        childItem = parentNode.child(row)
        if childItem:
            return self.createIndex(row, column, childItem)
        else:
            return QModelIndex()

    def getNode(self, index):
        """CUSTOM; 
        INPUTS: QModelIndex"""
        if index.isValid():
            node = index.internalPointer()
            if node:
                return node
        return self._rootNode

    def insertRows(self, position, rows, parent=QModelIndex()):
        """INPUTS: int, int, QModelIndex
        """
        parentNode = self.getNode(parent)
        self.beginInsertRows(parent, position, position + rows - 1)
        for _ in range(rows):
            childCount = parentNode.childCount()
            childNode = Node("untitled" + str(childCount))
            success = parentNode.insertChild(position, childNode)
        self.endInsertRows()
        return success
    
    def removeRows(self, position, rows, parent=QModelIndex()):
        """INPUTS: int, int, QModelIndex"""
        parentNode = self.getNode(parent)
        self.beginRemoveRows(parent, position, position + rows - 1)
        for _ in range(rows):
            success = parentNode.removeChild(position)
        self.endRemoveRows()
        return success
    
    def nodeType(self, index):
        """INPUTS: QModelindex
        OUTPUTS: str (type of this node)
        """
        if not index.isValid():
            return None

        node = index.internalPointer()
        nodeType = node._typeinfo
        return nodeType
    
    def findValue(self, parent_index, value, role = Qt.DisplayRole):
        """finds the first index of a given value under parent_index 
        INPUTS: QModelIndex, Str, role
        OUTPUTS: QModelIndex
        """
        for i in range(self.rowCount(parent_index)):
            index = self.index(i, 0, parent_index)
            data = self.data(index, role)
            if data == value:
                return index
        return QModelIndex()
    

class NavigationModel(TreeModel):
    def __init__(self, root, parent=None):
        super().__init__(root, parent)
    
    def data(self, index, role):
        """INPUTS: QModelIndex, int,
        OUTPUT: QVariant, strings are cast to QString which is a QVariant"""
        if not index.isValid():
            return None

        node = index.internalPointer()
        if role == Qt.DisplayRole or role == Qt.EditRole:
            if index.column() == 0:
                return node.name()
            
        if role == Qt.DecorationRole:
            if index.column() == 0:
                typeInfo = node._typeinfo
                if typeInfo == "Sample":
                    status = node.status.lower()
                    category = general.allele_status_dic[status]
                    try:
                        icon_path = general.icon_dic[category]
                    except KeyError:
                        icon_path = general.icon_dic["error"]
                    return QIcon(icon_path)
                

class Navigation(QWidget):
    """a navigation widget, 
    displaying all known projects and samples
    """
    changed_projects = pyqtSignal(str, str)
    changed_allele = pyqtSignal(str, int, str)
    change_view = pyqtSignal(int)
    refresh = pyqtSignal(str)
    
    def __init__(self, log, settings):
        self.log = log
        self.settings = settings
        super().__init__()
        self.init_UI()
        self.create_model()
        self.tree.expand(self.open_node)
        self.tree.clicked.connect(self.onClicked)
        
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.open_menu)
        
    def init_UI(self):
        """creates the UI
        """
        self.log.debug("Setting up Navigation area UI...")
        self.tree = QTreeView()
        self.tree.doubleClicked.connect(self.onDoubleClick)
        self.grid = QGridLayout()
        self.setLayout(self.grid)
        self.header_lbl = QLabel("Projects and Samples:", self)
        self.header_lbl.setStyleSheet(general.label_style_2nd)
        self.grid.addWidget(self.header_lbl, 0,0)
        
        self.grid.addWidget(self.tree, 1, 0)
        header = self.tree.header()
        header.hide()
        self.log.debug("\t=> Done!")
        
    def create_model(self):
        """creates or recreates the model
        """
        self.log.debug("Updating Navigation area...")
        root_node = Node("All")
        openNode = Node("Open", root_node)
        closedNode = Node("Closed", root_node)
        project_nodes = {}
        
        query = """select distinct sample_id_int, projects.project_name, project_status, allele_status, allele_nr 
        from projects left join alleles
            on projects.project_name = alleles.project_name 
        order by project_status desc, projects.project_name desc, sample_id_int
        """
        q = QtSql.QSqlQuery()
        q.exec_(query)
        while q.next():
            sample = q.value(0)
            project = q.value(1)
            pstatus = q.value(2)
            astatus = q.value(3)
            nr = q.value(4)
            try:
                pnode = project_nodes[project]
            except KeyError:
                if pstatus == "Closed":
                    topnode = closedNode
                else:
                    topnode = openNode
                pnode = Node(project, topnode, "Project")
                project_nodes[project] = pnode
            if sample:
                if nr != 1:
                    sample = "{} ({})".format(sample, nr)
                Node(sample, pnode, "Sample", astatus)
        
        self.model = NavigationModel(root_node)
        self.tree.setModel(self.model)
        
        self.open_node = self.model.index(0, 0, QModelIndex())
        self.closed_node = self.model.index(1, 0, QModelIndex())
        self.root_node = self.open_node.parent()
        self.log.debug("\t=> Done!")
        
    @pyqtSlot(str, str)
    def expand_project(self, project, status = None):
        """expands the node of the given project, 
        returns its index and parent-node's index 
        """
        self.log.debug("Expanding project {} ({})...".format(project, status))
        if not status in (None, "Open", "Closed"):
            return None, None
        myindex = self.open_node
        myparent_node = self.open_node
        if status == "Open":
            self.log.debug("Open")
            parent_node = self.open_node
            self.tree.expand(parent_node)
            self.tree.collapse(self.closed_node)
        elif status == "Closed":
            self.log.debug("Closed")
            parent_node = self.closed_node
            self.tree.expand(parent_node)
            self.tree.collapse(self.open_node)
        
        else: # figure out whether project is open or closed
            self.log.debug("Status unknown...")
            try:
                for i in range(self.model.rowCount(self.root_node)):
                    parent_node = self.model.index(i, 0, self.root_node)
                    status = self.model.data(parent_node, Qt.DisplayRole)
                    
                    for row in range(self.model.rowCount(parent_node)):
                        index = self.model.index(row, 0, parent_node)
                        myproj = self.model.data(index, Qt.DisplayRole)
                        if myproj == project:
                            myindex = index
                            myparent_node = parent_node 
                            self.tree.expand(myindex)
            except Exception as E:
                self.log.error(E)
                self.log.exception(E)
        self.select_project(project)
        self.log.debug("\t=> project found ({}) and successfully expanded".format(status))
        return myindex, myparent_node
    
    @pyqtSlot(QModelIndex)
    def onClicked(self, index):
        """emits signals when a project or sample is selected
        """
        data = self.model.data(index, Qt.DisplayRole)
        nodetype = self.model.nodeType(index)
        if nodetype == "Sample":
            if ("(") in data:
                data = data.split("(")
                sample = data[0].strip()
                nr = int(data[1].strip()[:-1])
            else:
                sample = data
                nr = 1
            project = self.model.data(self.model.parent(index), Qt.DisplayRole)
            self.changed_allele.emit(sample, nr, project)
            self.log.debug("Navigation emitted 'Allele changed to {} #{} (project {})'".format(sample, nr, project))
        elif nodetype == "Project":
            status = self.model.data(self.model.parent(index), Qt.DisplayRole)
            self.changed_projects.emit(data, status)
            self.log.debug("Navigation emitted 'Project changed to {}'".format(data))
    
    @pyqtSlot(QPoint)
    def open_menu(self, pos):
        """provides a context menu
        """
        index = self.tree.indexAt(pos)
        nodetype = self.model.nodeType(index)
        self.log.debug("Opening navigation menu...")
        if nodetype == "Project":
            menu = QMenu()
            open_project_act = menu.addAction("Open Project View")
            action = menu.exec_(self.tree.mapToGlobal(pos))
            
            if action == open_project_act:
                project = self.model.data(index, Qt.DisplayRole)
                status = self.model.data(self.model.parent(index), Qt.DisplayRole)
                self.changed_projects.emit(project, status)
                self.change_view.emit(3)
                self.log.debug("Navigation emitted changed_projects & change_view to ProjectView")
            
        elif nodetype == "Sample":
            menu = QMenu()
            open_sample_act = menu.addAction("Open Sample View")
            delete_sample_act = menu.addAction("Delete Allele (admin-only!)")
            action = menu.exec_(self.tree.mapToGlobal(pos))
            
            if action:
                sample_list = self.model.data(index, Qt.DisplayRole).split()
                sample = sample_list[0]
                if len(sample_list) > 1:
                    nr = int(sample_list[1][1:-1])
                else:
                    nr = 1
                project = self.model.data(self.model.parent(index), Qt.DisplayRole)
                status = self.model.data(self.model.parent(self.model.parent(index)), Qt.DisplayRole)
                if action == open_sample_act:
                    try:
                        self.changed_allele.emit(sample, nr, project)
                        self.change_view.emit(4)
                        self.log.debug("Navigation emitted changed_alleles & change_view to AlleleView")
                    except Exception as E:
                        self.log.exception(E)
                elif action == delete_sample_act:
                    self.log.info("Deleting {} #{} of project {}".format(sample, nr, project))
                    self.delete_sample(sample, nr, project, status)
    
    @pyqtSlot(QModelIndex)
    def onDoubleClick(self, index):
        """open SampleView or ProjectView
        """
        nodetype = self.model.nodeType(index)
        if nodetype == "Project":
            project = self.model.data(index, Qt.DisplayRole)
            status = self.model.data(self.model.parent(index), Qt.DisplayRole)
            self.changed_projects.emit(project, status)
            self.change_view.emit(3)
            self.log.debug("Navigation emitted changed_projects & change_view to ProjectView")
            
        elif nodetype == "Sample":
            sample_list = self.model.data(index, Qt.DisplayRole).split()
            sample = sample_list[0]
            if len(sample_list) > 1:
                nr = int(sample_list[1][1:-1])
            else:
                nr = 1
            project = self.model.data(self.model.parent(index), Qt.DisplayRole)
            status = self.model.data(self.model.parent(self.model.parent(index)), Qt.DisplayRole)
            self.changed_allele.emit(sample, nr, project)
            self.change_view.emit(4)
            self.log.debug("Navigation emitted changed_alleles & change_view to AlleleView")
                    
    @pyqtSlot(str)
    def select_project(self, project):
        """looks for <project> in the tree-model and selects it if found;
        selects it and returns its index 
        """
        for top_node in [self.open_node, self.closed_node]:
            index = self.model.findValue(top_node, project)
            if index.isValid():
                self.tree.setCurrentIndex(index)
                return index
        return QModelIndex()
        
    @pyqtSlot(str)
    def select_sample(self, project, sample, nr):
        """looks for <sample> in <project> in the tree-model and selects it if found;
        selects it and returns its index
        """
        pindex = self.select_project(project)
        if int(nr) > 1:
            sample = "{} ({})".format(sample, nr)
        index = self.model.findValue(pindex, sample)
        if index.isValid():
            self.tree.setCurrentIndex(index)
            return index       
        return QModelIndex()
    
    def delete_sample(self, sample, nr, project, status):
        """delete a sample from the database & file system
        """
        self.log.debug("Attempting to delete sample '{}' allele {} of project '{}' from database...".format(sample, nr, project))
        if self.settings["login"] == "admin":
            pass
        else:
            pwd, ok = QInputDialog.getText(self, "Enter Password", "Please provide password:", QLineEdit.Password)
            if ok:
                if pwd == "ichdarfdas":
                    pass
                else:
                    return
            else:
                return
        self.log.debug("Asking for confirmation before deleting allele...")
        reply = QMessageBox.question(self, 'Message',
            "Are you really sure you want to delete sample {} allele #{} from project {}?".format(sample, nr, project), QMessageBox.Yes | 
            QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            # delete from database:
            delete_q_alleles = "delete from alleles where sample_id_int = '{}' and allele_nr = {} and project_name = '{}'".format(sample, nr, project)
            success, _ = db_internal.execute_query(delete_q_alleles, 0, self.log, "Deleting sample {} allele #{} from ALLELES table".format(sample, nr), "Sample Deletion Error", self)
            if success:
                self.log.debug("\t=> Successfully deleted sample from table ALLELES")
            
            more_projects_query = "select project_name from alleles where sample_id_int = '{}'".format(sample)
            success, data = db_internal.execute_query(more_projects_query, 1, self.log, "Finding more rows with sample {} in ALLELES table".format(sample), "Sample Deletion Error", self)
            
            single_allele = False
            if success:
                if not data: # sample was only contained in this project and only had one allele
                    single_allele = True
                    delete_q_samples = "delete from SAMPLES where sample_id_int = '{}'".format(sample)
                    success, _ = db_internal.execute_query(delete_q_samples, 0, self.log, "Deleting sample {} from SAMPLES table".format(sample), "Sample Deletion Error", self)
                    if success:
                        self.log.debug("\t=> Successfully deleted sample from table SAMPLES")
                
                files_q = "select raw_file, fasta, blast_xml, ena_file, ena_response_file, ipd_submission_file from FILES where sample_id_int = '{}' and allele_nr = {}".format(sample, nr)
                success, files = db_internal.execute_query(files_q, 6, self.log, "Getting files of sample {} #{} from FILES table".format(sample, nr), "Sample Deletion Error", self)
                if success:
                    
                    delete_q_files = "delete from FILES where sample_id_int = '{}' and allele_nr = {}".format(sample, nr)
                    success, _ = db_internal.execute_query(delete_q_files, 0, self.log, "Deleting sample {} from FILES table".format(sample), "Sample Deletion Error", self)
                    if success:
                        self.log.debug("\t=> Successfully deleted sample from table FILES")
            
            # delete from disk space:
            self.log.debug("Attempting to delete sample {} allele #{} of project '{}' from file system...".format(sample, nr, project))
            sample_dir = os.path.join(self.settings["projects_dir"], project, sample)
            if files:
                for myfile in files[0]:
                    if myfile:
                        self.log.debug("\tDeleting {}...".format(myfile))
                        try:
                            os.remove(os.path.join(sample_dir, myfile))
                        except Exception:
                            self.log.debug("\t\t=> Could not delete")
            
            if single_allele:
                self.log.debug("\tDeleting sample dir {}...".format(sample_dir))
                os.removedirs(sample_dir)
            self.log.debug("=> Sample {} #{} of project {} successfully deleted from database and file system".format(sample, nr, project))
            self.refresh.emit(project)
            self.changed_projects.emit(project, status)

#===========================================================
# main:
def main():
    from typeloader_GUI import create_connection, close_connection, log_uncaught_exceptions
    import GUI_login
    log = general.start_log(level="DEBUG")
    log.info("<Start {} V{}>".format(os.path.basename(__file__), __version__))
    sys.excepthook = log_uncaught_exceptions
    settings_dic = GUI_login.get_settings("admin", log)
    mydb = create_connection(log, settings_dic["db_file"])
    app = QApplication(sys.argv)
    ex = Navigation(log, settings_dic)
#     ex.select_project("bla")
#     ex.select_sample("20180328_BS_mixed_PB3", "ID10354372", 1)
    ex.show()
    
    result = app.exec_()
    
    close_connection(log, mydb)
    log.info("<End>")
    sys.exit(result)


if __name__ == '__main__':
    main()
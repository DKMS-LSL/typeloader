#!/usr/bin/env python3
# -*- coding: cp1252 -*-
'''
Created on 13.03.2018

widgits_misc.py

misc widgets for TypeLoader

@author: Bianca Schoene
'''

# import modules:

import sys, os
from PyQt5.QtWidgets import (QApplication, QSizePolicy, QGridLayout, 
                             QLabel, QPushButton, QMessageBox)
from PyQt5.Qt import (QWidget, pyqtSlot, QVBoxLayout, pyqtSignal,
                      QHBoxLayout, QSpacerItem)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt
import general

#===========================================================
# parameters:

from __init__ import __version__
#===========================================================
# classes:

    
class UnderConstruction(QWidget):
    """a Widgit to show that something is not implemented, yet
    """
    def __init__(self, log):
        """constructor
        """
        super().__init__()
        self.log = log
        self.initUI()
        
    def initUI(self):
        """define the GUI
        """  
        grid = QGridLayout()
        self.setLayout(grid)
        self.resize(300,30)
        
        pixmap = QPixmap(os.path.join("icons", "construction.png"))
        self.pic_lbl = QLabel(self)
        self.pic_lbl.setPixmap(pixmap)
        grid.addWidget(self.pic_lbl, 0, 0)
        
        self.text = QLabel("Sorry, this does not work, yet! :-(", self)
        self.text.setStyleSheet(general.label_style_main)
        self.text.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        grid.addWidget(self.text, 0, 1)
        
        self.show()


class ConfirmResetButton(QPushButton):
    """a QPushButton that can be used to confirm or reset changes in the models of all widgets listed in widgets
    (for all widgets, these models must be called self.model)
    """
    confirmed = pyqtSignal()
    def __init__(self, text, purpose, widgets, log, parent= None):
        super().__init__(parent)
        self.setText(text)
        self.log = log
        purpose = purpose.lower()
        if purpose in ["confirm", "reset"]:
            self.purpose = purpose
        else:
            self.log.error("ConfirmResetButton purpose must be confirm or reset!")
        self.widgets = widgets
        self.clicked.connect(self.execute)
        for widget in widgets:
            widget.model.dataChanged.connect(self.highlight)
    
    @pyqtSlot()
    def highlight(self):
        """trigger this slot if unconfirmed data exists
        """ 
        self.setStyleSheet(general.btn_style_clickme)
    
    @pyqtSlot()
    def normalize(self):
        """trigger this slot if no unconfirmed data exists
        """ 
        self.setStyleSheet(general.btn_style_normal)
    
    @pyqtSlot()
    def execute(self):
        """executes this button's job
        """
        error = False
        for widget in self.widgets:
            if self.purpose == "confirm":
                try:
                    success = widget.model.submitAll()
                    self.log.debug("\t=> All changes commited")
                    self.confirmed.emit()
                except Exception as E:
                    QMessageBox.warning(self, "Confirmation error", "Cannot confirm:\n\n{}".format(repr(E)))
                    self.log.exception(E)
            else:
                try:
                    success = widget.model.revertAll()
                    self.log.debug("\t=> All changes reverted")
                except Exception as E:
                    QMessageBox.warning(self, "Reversion error", "Cannot revert changes:\n\n{}".repr(E))
                    self.log.exception(E)
            if not success:
                lasterr = widget.model.lastError()
                if lasterr.isValid():
                    self.log.error("ERROR: Cannot update {}: {}".format(str(type(widget)), lasterr.text()))
                    QMessageBox.warning(self, "Database update error", "Cannot update database:\n\n{}".format(lasterr.text()))
                    error = True
                    #widget.model.revertAll()
                    #FIXME: (future) do users want this?
        if not error:
            self.normalize()


class ConfirmResetWidget(QWidget):
    """a widget containing a confirm button and a reset button,
    which will commit or reset all data in self.model of all widgets given in widgets;
    direction specifies how to arrange the buttons
    """
    data_changed = pyqtSignal(bool)
    
    def __init__(self, widgets, log, direction = Qt.Horizontal, parent= None, stretch = 0):
        super().__init__(parent)
        self.widgets = widgets
        self.log = log
        self.direction = direction
        self.stretch = stretch
        self.init_UI()
    
    def init_UI(self):
        """create both buttons, arrange them and connect them
        """
        if self.direction == Qt.Horizontal:
            layout = QHBoxLayout()
            spacer_width = self.stretch
            spacer_height = 1
        else:
            layout = QVBoxLayout()
            spacer_width = 1
            spacer_height = self.stretch
        self.setLayout(layout)
        
        self.confirm_btn = ConfirmResetButton("Confirm all changes", "confirm", self.widgets, self.log, self)
        self.confirm_btn.clicked.connect(self.on_data_changed)
        layout.addWidget(self.confirm_btn)
        
        if self.stretch:
            layout.addSpacerItem(QSpacerItem(spacer_width, spacer_height, QSizePolicy.Expanding, QSizePolicy.Expanding))
        
        self.reset_btn = ConfirmResetButton("Reset all changes", "reset", self.widgets, self.log, self)
        self.reset_btn.clicked.connect(self.on_data_changed)
        layout.addWidget(self.reset_btn)
        
        for widget in self.widgets:
            widget.model.dataChanged.connect(self.on_data_changed)
        self.confirm_btn.clicked.connect(self.reset_btn.normalize)
        self.reset_btn.clicked.connect(self.confirm_btn.normalize)
        
    def on_data_changed(self):
        if self.sender() in (self.confirm_btn, self.reset_btn):
            self.data_changed.emit(False) # data no longer unconfirmed
        else:
            self.data_changed.emit(True)


def settings_ok(category, all_settings, log):
    """checks whether necessary settings have been defined
    """
    log.debug("Checking if {} settings are configured...".format(category))
    if category == "ENA":
        relevant_settings = {"xml_center_name" : "Company Name (for ENA)",
                             "ftp_user" : "FTP user",
                             "ftp_pwd" : "FTP Password"
                             }
    elif category == "IPD":
        relevant_settings = {"submittor_id" : "IPD Submittor ID",
                             "lab_contact_address" : "Lab Contact's Form of Address",
                             "lab_contact" : "Lab Contact for IPD",
                             "lab_contact_email": "Lab Contact Email",
                             "lab_of_origin" : "Company Name (for IPD)"}
    
    else:
        msg = "I don't know how to check '{}' settings!".format(category)
        raise ValueError(msg)
        return False, msg
 
    missing_settings = []
    for key in relevant_settings:
        value = all_settings[key]
        if value.strip() == "":
            missing_settings.append(relevant_settings[key])
            
    if missing_settings:
        log.warning("Missing {} settings: {}".format(category, ",".join(missing_settings)))
        msg = "Please specify the following settings under Settings => Company:\n"
        for item in missing_settings:
            msg += " - {}\n".format(item)
        if category == "IPD":
            msg += "\nAlso, make sure all settings under Settings => Method reflect your workflow accurately.\n"
        msg += "\nThen try again."
        return False, msg
    log.debug("\t=> ok")
    return True, None

pass
#===========================================================
# main:
        
if __name__ == '__main__':
    log = general.start_log(level="DEBUG")
    log.info("<Start {} V{}>".format(os.path.basename(__file__), __version__))
    
    app = QApplication(sys.argv)
    ex = ConfirmResetWidget([], None, direction = Qt.Vertical, parent= None, stretch = 200)
    ex.show()
    result = app.exec_()
    log.info("<End>")
    sys.exit(result)
#     sys.exit(app.exec_())

    
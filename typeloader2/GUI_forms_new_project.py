#!/usr/bin/env python3
# -*- coding: cp1252 -*-
'''
Created on 13.03.2018

GUI_forms.py

widgits for adding new sequences or new projects to TypeLoader

@author: Bianca Schoene
'''

# import modules:

import sys, os, shutil, re
from PyQt5.QtSql import QSqlQuery
from PyQt5.QtWidgets import (QApplication, QFormLayout, QPushButton, QLineEdit, QDialog,
                             QMessageBox)
from PyQt5.Qt import pyqtSlot, pyqtSignal
from PyQt5.QtGui import QIcon

from typeloader2 import general, db_internal, typeloader_functions
from typeloader2.GUI_misc import settings_ok

# ===========================================================
# parameters:

# ===========================================================
# classes:

class NewProjectForm(QDialog):
    """a popup widget to create a new Typeloader Project
    """
    project_changed = pyqtSignal(str)
    refresh_projects = pyqtSignal()

    def __init__(self, log, mydb, settings, parent=None):
        try:
            super().__init__(parent)
            self.settings = settings
            log.debug("Opening 'New Project' Dialog...")
            self.log = log
            self.mydb = mydb
            self.init_UI()
            self.setWindowTitle("Create a new project")
            self.setWindowIcon(QIcon(general.favicon))
            if self.settings["modus"] == "debugging":
                self.fill_with_test_values()
            self.get_existing_projects()
            self.user = ""
            self.gene = ""
            self.pool = ""
            self.project_name = None
            self.submission_file = None
            self.success = False
            self.invalid_fields = []
            self.output_file = None
            self.show()
            ok, msg = settings_ok("ENA", self.settings, self.log)
            if not ok:
                QMessageBox.warning(self, "Missing ENA settings", msg)
                self.close()
        except Exception as E:
            QMessageBox.warning(self, "Problem with NewProjectForm", "Could not open NewProjectForm:\n\n" + repr(E))
            log.error(E)
            log.exception(E)

    def init_UI(self):
        """establish the widgets
        """
        layout = QFormLayout()
        self.setLayout(layout)

        self.user_entry = QLineEdit(self.settings["user_name"], self)
        self.user_entry.setWhatsThis("Your name")
        layout.addRow("User:", self.user_entry)
        self.user_entry.setText(self.settings["user_name"])

        self.gene_entry = QLineEdit(self)
        self.gene_entry.setFocus()
        self.gene_entry.setMinimumWidth(175)
        layout.addRow("Gene:", self.gene_entry)
        self.gene_entry.setWhatsThis("The gene analyzed in this project. Use 'mixed' for multiple genes.")

        self.pool_entry = QLineEdit(self)
        layout.addRow("Pool:", self.pool_entry)
        self.pool_entry.setWhatsThis("Name for the sample pool, required by ENA.")
        self.pool_entry.textChanged.connect(self.check_ready_project)

        self.title_entry = QLineEdit(self)
        layout.addRow("Title:", self.title_entry)
        self.title_entry.setPlaceholderText("(optional)")
        self.title_entry.setWhatsThis(
            "An optional short project title. If you set none, a default text is generated for ENA.")

        self.desc_entry = QLineEdit(self)
        layout.addRow("Description:", self.desc_entry)
        self.desc_entry.setPlaceholderText("(optional)")
        self.desc_entry.setWhatsThis("An optional project description. Useful for later filtering.")

        self.project_btn = QPushButton("Click to generate", self)
        layout.addRow("Project Name:", self.project_btn)
        self.project_btn.setEnabled(False)
        self.project_btn.clicked.connect(self.on_projectBtn_clicked)
        self.project_btn.setWhatsThis(
            "Click here to generate the project name. Can only be clicked after all necessary fields above have been filled.")

        self.submit_btn = QPushButton("Start new project", self)
        layout.addRow(self.submit_btn)
        self.submit_btn.setEnabled(False)
        self.submit_btn.clicked.connect(self.on_submitBtn_clicked)
        self.submit_btn.setWhatsThis(
            "Click here to submit the project to ENA, receive a project accession number, and save the project. Can only be clicked after a project name has been generated.")

        self.acc_entry = QLineEdit(self)
        layout.addRow("ENA Project Nr.:", self.acc_entry)
        self.acc_entry.setWhatsThis("Project accession number received from ENA.")

        self.close_btn = QPushButton("Done", self)
        layout.addRow(self.close_btn)
        self.close_btn.clicked.connect(self.close_me)
        self.close_btn.setWhatsThis("Click to leave this dialog.")

    @pyqtSlot()
    def check_ready_project(self):
        """check whether all required fields have content;
        if yes, enable project_btn
        """
        self.user = self.user_entry.text()
        self.gene = self.gene_entry.text()
        self.pool = self.pool_entry.text()

        if self.user and self.gene and self.pool:
            self.project_btn.ready = True
            self.project_btn.setEnabled(True)
            self.project_btn.setStyleSheet(general.btn_style_ready)

    def get_existing_projects(self):
        """gets a list of all existing projects
        """
        self.log.debug("Getting all existing projects from database...")
        query = "select project_name from projects"
        success, data = db_internal.execute_query(query, 1, self.log,
                                                  "retrieving existing projcts",
                                                  "Database error", self)
        self.existing_projects = []
        if success:
            if data:
                self.existing_projects = [project for (project,) in data]

    def get_values(self):
        """retrieves all values from the GUI
        """
        self.log.debug("Getting all infos from the GUI...")
        self.check_ready_project()
        self.title = self.title_entry.text().strip()
        self.description = self.desc_entry.text().strip()
        if not self.title:
            self.title = self.pool
            self.title_entry.setText(self.pool)

    def check_all_fields_valid(self):
        """checks whether all fields contain only valid characters
        """
        self.log.debug("\tChecking whether all fields are ok...")
        self.invalid_fields = []
        allowed_characters = '^[a-zA-Z0-9-]+$'  # only alphanumeric characters or hyphens

        fields_to_test = [("gene", self.gene), ("pool", self.pool)]
        for (field, value) in fields_to_test:
            valid = re.match(allowed_characters, value)
            if not valid:
                self.invalid_fields.append(field)
                self.log.info("=> invalid character found in {}: {}!".format(field, value))

        secondary_fields = [("user name", self.user), ("title", self.title), ("description", self.description)]
        allowed_characters = '^[a-zA-Z0-9- ]+$'  # these may also contain spaces
        for (field, value) in secondary_fields:
            if value:
                valid = re.match(allowed_characters, value)
                if not valid:
                    self.invalid_fields.append(field)
                    self.log.info("\t=> invalid character found in {}: {}!".format(field, value))

        invalid_msg = ""
        if self.invalid_fields:
            invalid_fields = " and ".join(self.invalid_fields)
            invalid_msg = "Invalid character found in {}!\n".format(invalid_fields)
            invalid_msg += "Please don't use anything but letters, numbers or hyphens in your fields.\n"
            invalid_msg += "(Title, description and user name may also contain spaces.)"
        else:
            self.log.debug("\t=> everything ok")

        return invalid_msg

    @pyqtSlot()
    def on_projectBtn_clicked(self):
        """generates project_name out of given fields & displays it on itself
        """
        self.log.debug("Generating project name...")
        self.check_ready_project()
        self.get_values()

        invalid_msg = self.check_all_fields_valid()
        if invalid_msg:
            QMessageBox.warning(self, "Invalid character in {}".format(" and ".join(self.invalid_fields)), invalid_msg)
            return False

        success, err_type, self.project_name = typeloader_functions.create_project_name(
            self.user, self.gene, self.pool, self.settings, self.log)
        if not success:
            msg = self.project_name
            QMessageBox.warning(self, err_type, msg)
            return

        if self.project_name in self.existing_projects:
            self.log.warning(f"Project '{self.project_name}' already exists! Choose a different pool name!")
            QMessageBox.warning(self, "Project name not unique!",
                                f"A project named '{self.project_name}' already exists! \n"
                                f"Please choose a different pool name.")
            return

        else:
            self.project_btn.setText(self.project_name)
            self.submit_btn.setEnabled(True)
            self.submit_btn.setStyleSheet(general.btn_style_ready)
            self.project_btn.setStyleSheet(general.btn_style_normal)

    @pyqtSlot()
    def on_submitBtn_clicked(self):
        """submits data to ENA & shows the accession-ID
        """
        try:  # for debugging
            success, err_type, msg, self.project_dir, self.project_filename = typeloader_functions.create_project(
                self.project_name,
                self.title,
                self.description,
                self.gene,
                self.pool,
                self.user,
                self.settings,
                self.log)

            if success:
                self.accession_ID = msg
                self.acc_entry.setText(self.accession_ID)
                self.close_btn.setStyleSheet(general.btn_style_ready)
                self.submit_btn.setStyleSheet(general.btn_style_normal)
                self.success = True

            else:
                self.log.warning(err_type)
                self.log.info(msg)
                if err_type == "Project exists in db":
                    self.project_btn.setText(msg)
                    self.project_btn.setStyleSheet(general.btn_style_clickme)
                    self.submit_btn.setEnabled(False)
                    self.accession_ID = ""
                    self.acc_entry.setText(self.accession_ID)

                else:  # did not even reach ENA:
                    QMessageBox.warning(self, err_type, msg)
                    self.submit_btn.setEnabled(False)

        except Exception as E:
            self.log.error("Error in ENA project submission!")
            self.log.exception(E)

        if not self.success:
            self.log.info(f"Project creation was not successful. Removing all files from {self.project_dir}...")
            try:
                shutil.rmtree(self.project_dir)
            except Exception as E:
                self.log.debug("=> File deletion did not work:")
                self.log.error(E)
                self.log.exception(E)
                pass

        else:
            self.log.debug("=> Added to database successfully")
            self.success = True
        return self.success

    def fill_with_test_values(self):
        """for debugging/development
        """
        self.gene_entry.setText("HLA-B")
        self.pool_entry.setText("NEB1")

    @pyqtSlot()
    def close_me(self):
        """emits project-changed before closing the dialog
        """
        if self.project_name:
            self.project_changed.emit(self.project_name)
            self.refresh_projects.emit()
            self.log.debug("'Project_changed' emitted")
        self.close()


# ===========================================================
# main:

if __name__ == '__main__':
    from typeloader_GUI import create_connection, close_connection
    import GUI_login

    log = general.start_log(level="DEBUG")
    log.info("<Start {}>".format(os.path.basename(__file__)))

    settings_dic = GUI_login.get_settings("admin", log)
    mydb = create_connection(log, settings_dic["db_file"])

    app = QApplication(sys.argv)
    ex = NewProjectForm(log, mydb, settings_dic)
    ex.show()

    result = app.exec_()
    close_connection(log, mydb)
    log.info("<End>")
    sys.exit(result)
#     sys.exit(app.exec_())

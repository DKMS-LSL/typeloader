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

import general
from typeloader_core import EMBLfunctions as EF
from GUI_misc import settings_ok

import db_internal


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
        if self.user == self.settings["user_name"]:
            initials = self.settings["short_name"]
        else:
            initials = "".join(word[0].upper() for word in self.user.split())

        date = general.timestamp("%Y%m%d")

        self.get_values()
        invalid_msg = self.check_all_fields_valid()
        if invalid_msg:
            QMessageBox.warning(self, "Invalid character in {}".format(" and ".join(self.invalid_fields)), invalid_msg)
            return False

        try:
            self.project_name = "_".join([date, initials, self.gene, self.pool])
            self.project_name = self.project_name.replace(" ", "-")
        except Exception as E:
            self.log.error(E)
            QMessageBox.warning(self, "Cannot create project name!",
                                "Cannot create a project name with the given parameters (see error below).\nPlease adjust them!\n\n{}".format(
                                    E))
            return

        self.log.debug("=> project name {} assigned".format(self.project_name))
        if self.project_name in self.existing_projects:
            self.log.warning("Project '{}' already exists! Choose a different pool name!".format(self.project_name))
            QMessageBox.warning(self, "Project name not unique!",
                                """A project named '{}' already exists!\nPlease choose a different pool name.
                                """.format(self.project_name))
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
            self.log.debug("Submitting project to ENA...")
            ## create variables
            successful_transmit = "false"
            xml_center_name = self.settings["xml_center_name"]

            ## Creating XML files
            self.project_dir = os.path.join(self.settings["projects_dir"], self.project_name)
            self.log.debug("Creating {}".format(self.project_dir))
            try:
                os.makedirs(self.project_dir)
            except WindowsError:
                self.log.warning("'{}' already exists".format(self.project_dir))
            self.project_xml = EF.generate_project_xml(self.title, self.description, self.project_name, xml_center_name)
            self.project_filename = os.path.join(self.project_dir, self.project_name + ".xml")

            if os.path.exists(self.project_filename):
                info_exists = "File '{}' already exist. Please change pool name.".format(self.project_filename)
                QMessageBox.warning(self, "ALIAS already exists!", info_exists)
                self.log.warning("File " + self.project_filename + " already exist, use another pool name")
            else:
                success = EF.write_file(self.project_xml, self.project_filename, self.log)
                if not success:
                    msg = "Could not write to {}!".format(self.project_filename)
                    QMessageBox(self, "Error writing project xml file!", msg)
                else:
                    submission_alias = self.project_name + "_sub"
                    submission_project_xml = EF.generate_submission_project_xml(submission_alias, xml_center_name,
                                                                                self.project_filename)
                    self.submission_file = os.path.join(self.project_dir, submission_alias + ".xml")
                    success = EF.write_file(submission_project_xml, self.submission_file, self.log)

                    if not success:
                        msg = "Could not write to {}!".format(self.submission_file)
                        QMessageBox(self, "Error writing project submission xml file!", msg)
                    else:
                        ## Communicate with EMBL
                        self.log.info("Submitting new project to EMBL...")
                        server = self.settings["embl_submission"]
                        proxy = self.settings["proxy"]
                        self.output_file = os.path.join(self.project_dir, self.project_name + "_output.xml")

                        study_err = EF.submit_project_ENA(self.submission_file, self.project_filename, "PROJECT",
                                                          server, proxy, self.output_file,
                                                          self.settings["ftp_user"], self.settings["ftp_pwd"])
                        if study_err:
                            self.log.exception(study_err)
                            QMessageBox.warning(self, "Error during ENA submission!",
                                                "Project submission to ENA did not work:\n\n{}!".format(study_err))
                        else:
                            self.log.info("=> Submission sent, awaiting response...")
                            successful_transmit, self.submission_ID, info_xml, error_xml, _ = EF.parse_register_EMBL_xml(
                                self.output_file, "SUBMISSION")
                            successful_transmit, self.accession_ID, info_xml, error_xml, _ = EF.parse_register_EMBL_xml(
                                self.output_file, "PROJECT")
                            # TODO: (future) cleanup: put all parsing into one function, add EXT_ID

                            if error_xml:
                                if info_xml == "known error":
                                    error_msg = error_xml
                                elif error_xml == "Internal Server Error":
                                    error_msg = "Internal Server Error.\nPlease check https://wwwdev.ebi.ac.uk/ena/submit/webin/login for details."
                                elif isinstance(error_xml, str):
                                    error_msg = error_xml
                                else:
                                    error_msg = "{}: {}".format(type(error_xml), str(error_xml))
                                self.log.error(error_xml)
                                self.log.exception(error_xml)
                                if "The object being added already exists in the submission account with accession" in error_xml:
                                    msg = "The project" + error_xml.split("The object")[1]
                                    msg += "\nPlease choose another pool name and try again!"
                                    QMessageBox.warning(self, "Project name already in use", msg)
                                else:
                                    QMessageBox.warning(self, "Error during ENA submission!",
                                                        "ENA response:\n\n{}".format(str(error_msg)))
                                successful_transmit = False
                                self.submit_btn.setEnabled(False)

                    if successful_transmit == "true":
                        self.log.debug("\t=> transmission to ENA successful")
                        success = self.add_project_to_db()
                        if success:
                            self.acc_entry.setText(self.accession_ID)
                            self.close_btn.setStyleSheet(general.btn_style_ready)
                            self.submit_btn.setStyleSheet(general.btn_style_normal)
                            self.success = True
                        else:
                            QMessageBox.warning(self, "Internal database problem",
                                                "Could not add project '{}' to the internal database!".format(
                                                    self.project_name))
                    else:
                        QMessageBox.warning(self, "ENA project submission failed",
                                            "ENA submission was not successful. Please try again!")
                        self.log.warning("ENA project submission failed!")
        except Exception as E:
            self.log.error("Error in ENA project submission!")
            self.log.exception(E)

        if not self.success:
            self.log.info("Project creation was not successful. Removing all files from {}...".format(self.project_dir))
            try:
                shutil.rmtree(self.project_dir)
            except Exception as E:
                self.log.debug("=> File deletion did not work:")
                self.log.error(E)
                self.log.exception(E)
                pass

    @pyqtSlot()
    def add_project_to_db(self):
        """adds all info about a project to the projects table
        """
        self.log.debug("Adding new project to database...")
        mydate = general.timestamp("%d.%m.%Y")
        query = """INSERT INTO projects VALUES
        ('{}', 'Open', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}');
        """.format(self.project_name, mydate, self.user, self.gene, self.pool,
                   self.title, self.description, self.accession_ID, self.submission_ID)
        q = QSqlQuery()
        q.exec_(query)

        lasterr = q.lastError()
        if lasterr.isValid():
            self.log.error(lasterr.text())
            if lasterr.text().startswith("UNIQUE constraint failed:"):
                self.project_btn.setText("Such a project exists already!")
                self.project_btn.setStyleSheet(general.btn_style_clickme)
                self.submit_btn.setEnabled(False)
                self.accession_ID = ""
                self.acc_entry.setText(self.accession_ID)
            success = False
        else:
            self.log.debug("=> Added to database successfully")
            success = True
        return success

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

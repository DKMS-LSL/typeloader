#!/usr/bin/env python3
# -*- coding: cp1252 -*-
'''
Created on 13.03.2018

GUI_forms.py

components for forms and dialogs

@author: Bianca Schoene
'''

# import modules:

import sys, os, shutil, time
from shutil import copyfile
from collections import namedtuple
from PyQt5.QtWidgets import (QApplication, QFileDialog, QGridLayout,
                             QPushButton, QMessageBox, QTextEdit,
                             QWidget, QHBoxLayout, QScrollArea,
                             QDialog, QLabel, QVBoxLayout, QGroupBox, QRadioButton,
                             QTableWidget, QTableWidgetItem)
from PyQt5.Qt import pyqtSlot, pyqtSignal
from PyQt5.QtGui import QIcon

import general, db_internal
from typeloader_core import make_imgt_files as MIF
from GUI_forms import (CollapsibleDialog, ChoiceSection, FileChoiceTable,
                       FileButton, ProceedButton, QueryButton, check_project_open)
from GUI_forms_submission_ENA import ProjectInfoTable
from GUI_misc import settings_ok
from GUI_functions_local import check_local, check_nonproductive, make_fake_ENA_file, get_pretypings_from_oracledb

# ===========================================================
# parameters:

# ===========================================================
# classes:

TargetAllele = namedtuple("TargetAllele", "gene target_allele partner_allele")


class AlleleChoiceBox(QWidget):
    """displays one target allele with multiple novel alleles,
    allows selecting the one pretyping representing the target allele
    """
    choice = pyqtSignal(tuple)

    def __init__(self, allele_info, log):
        super().__init__()
        [self.sample_id_int, self.local_name, self.allele, self.alleles] = allele_info
        self.log = log
        self.init_UI()

    def init_UI(self):
        layout = QHBoxLayout(self)
        self.setLayout(layout)
        name_lbl = QLabel(self.local_name + ":")
        layout.addWidget(name_lbl)

        box = QGroupBox("Which pretyping belongs to this allele?", self)
        box_layout = QHBoxLayout(box)
        box.setLayout(box_layout)
        layout.addWidget(box)
        self.options = []
        for a in self.alleles:
            btn = QRadioButton(a)
            box_layout.addWidget(btn)
            btn.clicked.connect(self.emit_choice)
            self.options.append(btn)

    @pyqtSlot()
    def emit_choice(self):
        """emits chosen pretyping for this target allele
        """
        pretyping = self.sender().text()
        self.log.info(" - {} is {}".format(self.local_name, pretyping))
        self.choice.emit((self.local_name, pretyping))


class BothAllelesNovelDialog(QDialog):
    """Popup created if target locus has more than 1 allele listed as novel
    """
    updated = pyqtSignal()

    def __init__(self, allele_dic, settings, log):
        log.info("BothAllelesNovelDialog created...")
        self.log = log
        self.settings = settings
        self.allele_dic = allele_dic
        super().__init__()

        self.setWindowTitle("Multiple novel alleles")
        self.setWindowIcon(QIcon(general.favicon))
        self.init_UI()
        self.show()

    def init_UI(self):
        """establish and fill the UI
        """
        self.log.info("Starting BothAllelesNovelDialog: Which pretyping is right for these alleles?")
        layout = QVBoxLayout(self)
        self.setLayout(layout)

        lbl1 = QLabel("Attention!")
        lbl1.setStyleSheet(general.label_style_2nd)
        layout.addWidget(lbl1)

        n = len(self.allele_dic)
        msg = "{} of the alleles to be submitted contain{} ".format(n, "s" if n == 1 else "")
        msg += "multiple novel alleles in the target locus.\n"
        msg += "Please indicate for each, which of the pretypings belongs to the allele you want to submit here!"
        lbl = QLabel(msg)
        lbl.setStyleSheet(general.label_style_normal)
        layout.addWidget(lbl)

        self.scrollArea = QScrollArea(self)
        self.scrollArea.setWidgetResizable(True)
        self.scrollAreaWidgetContents = QWidget(self.scrollArea)
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        scrollArea_layout = QVBoxLayout(self.scrollAreaWidgetContents)
        self.scrollAreaWidgetContents.setLayout(scrollArea_layout)

        layout.addWidget(self.scrollArea)

        self.choices_dic = {}
        self.choice_boxes = {}
        for allele in self.allele_dic:
            allele_info = self.allele_dic[allele]
            mybox = AlleleChoiceBox(allele_info, self.log)
            self.choice_boxes[allele] = mybox
            scrollArea_layout.addWidget(mybox)
            self.choices_dic[allele_info[1]] = False
            mybox.choice.connect(self.catch_choice)

        layout.addWidget(self.scrollArea)
        self.submit_btn = QPushButton("Save choices")
        self.submit_btn.setEnabled(False)
        self.submit_btn.clicked.connect(self.save_results)
        layout.addWidget(self.submit_btn)

    @pyqtSlot(tuple)
    def catch_choice(self, mysignal):
        """whenever a choice is made through a radiobutton,
        these are caught and stored in self.choices_dic[local_name] = pretyping
        """
        (local_name, pretyping) = mysignal
        alleles = self.allele_dic[local_name][-1]
        partner_allele = " and ".join([allele for allele in alleles if allele != pretyping])
        self.choices_dic[local_name] = (pretyping, partner_allele)
        self.check_ready()

    def check_ready(self):
        """checks if choices were made for all alleles;
        if yes, enables submit_btn
        """
        self.log.debug("Checking readiness...")
        ready = True
        for local_name in self.choices_dic:
            if not self.choices_dic[local_name]:
                ready = False
        if ready:
            self.log.debug("\t=> ready")
            self.submit_btn.setEnabled(True)
            self.submit_btn.setStyleSheet(general.btn_style_ready)
        else:
            self.log.debug("\t=> not ready")
            self.submit_btn.setEnabled(False)
            self.submit_btn.setStyleSheet(general.btn_style_normal)

    def save_results(self):
        """saves the user's choices in the db and emits signal
        """
        self.log.info("Saving choices to database...")
        for allele in self.allele_dic:
            [sample_id_int, local_name, allele_obj, _] = self.allele_dic[allele]
            choice = self.choices_dic[local_name]
            if "*" in choice[0]:
                (target, partner) = choice
            else:
                target = "{}*{}".format(allele_obj.gene, choice[0])
                partner = "{}*{}".format(allele_obj.gene, choice[1])
            query = """update ALLELES 
            set target_allele = '{}', partner_allele = '{}' 
            where local_name = '{}' and sample_id_int = '{}'""".format(target, partner, local_name, sample_id_int)
            success, _ = db_internal.execute_query(query, 0, self.log, "updating database", "Database error", self)
        if success:
            self.updated.emit()
            self.close()


class InvalidPretypingsDialog(QDialog):
    """Popup created if pretypings are not consistent with TypeLoader's assigned allele
    """
    ok = pyqtSignal()

    def __init__(self, allele_dic, settings, log):
        self.log = log
        self.settings = settings
        self.allele_dic = allele_dic
        super().__init__()

        self.setWindowTitle("Invalid pretypings")
        self.setWindowIcon(QIcon(general.favicon))
        self.resize(800, 400)
        self.init_UI()
        self.show()

    def init_UI(self):
        """establish and fill the UI
        """
        self.log.info("Starting InvalidPretypingsDialog: please adjust pretypings file for these alleles...")
        layout = QVBoxLayout(self)
        self.setLayout(layout)

        lbl1 = QLabel("Attention!")
        lbl1.setStyleSheet(general.label_style_2nd)
        layout.addWidget(lbl1)

        n = len(self.allele_dic)
        msg = "{} of the alleles to be submitted ha{} ".format(n, "s" if n == 1 else "ve")
        msg += "an invalid pretyping for the specfied locus.\n"
        msg += "Please adjust the pretypings file for each indicated sample, then try again!"
        lbl = QLabel(msg)
        lbl.setStyleSheet(general.label_style_normal)
        layout.addWidget(lbl)

        self.add_table(layout)

        self.ok_btn = QPushButton("Ok")
        self.ok_btn.clicked.connect(self.ok_clicked)
        self.ok_btn.setStyleSheet(general.btn_style_ready)
        layout.addWidget(self.ok_btn)

    def add_table(self, layout):
        """add and fill the table with problematic alleles
        """
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setRowCount(len(self.allele_dic))
        layout.addWidget(self.table)
        self.table.setHorizontalHeaderLabels(
            ["Sample", "Allele Name", "Locus", "Assigned Allele", "Pretyping", "Problem"])
        for n, allele in enumerate(self.allele_dic):
            i = 0
            for item in self.allele_dic[allele]:
                self.table.setItem(n, i, QTableWidgetItem(item))
                i += 1
        self.table.resizeColumnsToContents()

    def ok_clicked(self):
        self.log.debug("User clicked 'ok' on InvalidPretypingsDialog")
        self.ok.emit()
        self.close()


class IPDCounterLockedDialog(QMessageBox):
    """Popup created if IPD-counter is locked, allows removal of lock
    """
    remove_lock = pyqtSignal(bool)

    def __init__(self, parent, title, text, settings, log):
        self.log = log
        self.settings = settings
        super().__init__(parent)
        self.setIcon(QMessageBox.Warning)
        self.setText(text)
        self.setWindowTitle(title)
        self.init_UI()
        self.show()

    def init_UI(self):
        """establish and fill the UI
        """
        self.log.info("Starting IPDCounterLockedDialog...")

        self.setStandardButtons(QMessageBox.Cancel | QMessageBox.Ok)
        self.setDefaultButton(QMessageBox.Cancel)

        self.abort_txt = "Ok, I'll try again later."
        self.proceed_txt = "Proceed anyway."
        self.button(QMessageBox.Cancel).setText(self.abort_txt)
        self.button(QMessageBox.Ok).setText(self.proceed_txt)

        self.buttonClicked.connect(self.handle_click)

    def handle_click(self, button):
        """handles clicks on either of the buttons
        """
        txt = button.text()
        if txt == self.proceed_txt:
            self.proceed()
        elif txt == self.abort_txt:
            self.abort()

    def proceed(self):
        """asks for confirmation, then emits signal to remove lock file
        """
        self.log.info("User decision: remove lock on IPD_counter!")
        self.log.info("Are you sure?")
        reply = QMessageBox.question(self, "Please confirm",
                                     "Are you REALLY sure no other user is currently creating IPD files and you can continue safely?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            self.log.info("\t=> Yes, remove lock!")
            self.remove_lock.emit(True)
        else:
            self.log.info("\t=> No, I'd rather check again.")
            self.remove_lock.emit(False)

        self.close()

    def abort(self):
        """aborts the attempt
        """
        self.log.info("User decision: abort attempt for now and try again later.")
        self.remove_lock.emit(False)
        self.close()


class IPDFileChoiceTable(FileChoiceTable):
    """displays all alleles of a project
    so user can choose which to submit to IPD
    """
    old_cell_lines = pyqtSignal(dict)
    additional_info = pyqtSignal(dict)

    def __init__(self, project, log, parent=None):
        query = """select project_nr, alleles.sample_id_int, alleles.local_name, allele_status, 
        ena_submission_id, 
		case
			when instr(IPD_SUBMISSION_NR, '_') > 0
				then substr(IPD_SUBMISSION_NR, 1, instr(IPD_SUBMISSION_NR, '_')-1)
			else
				IPD_SUBMISSION_NR
		end as IPD_SUBMISSION_NR,
		cell_line_old, gene, target_allele, partner_allele
		from alleles
         join files on alleles.sample_id_int = files.sample_id_int and alleles.allele_nr = files.allele_nr
        """.format(project)  #TODO: is this format() still necessary or leftover code?
        num_columns = 10
        header = ["Submit?", "Nr", "Sample", "Allele", "Allele Status", "ENA submission ID", "IPD submission ID"]
        if parent:
            self.settings = parent.settings
        else:
            import GUI_login
            self.settings = GUI_login.get_settings("admin", log)

        super().__init__(project, log, header, query, num_columns,
                         myfilter=" order by project_nr ", allele_status_column=3,
                         instant_accept_status="ENA submitted", parent=self)

    def get_data(self):
        """get alleles from database
        """
        myquery = self.query + self.myfilter
        success, data = db_internal.execute_query(myquery, self.num_columns,
                                                  self.log, "retrieving data for FileChoiceTable from database",
                                                  "Database error", self)

        if success:
            self.data1 = data
        # add data based on cell_line_old:
        success, data2 = db_internal.execute_query(self.query + self.myfilter2, self.num_columns,
                                                   self.log, "retrieving data for FileChoiceTable from database",
                                                   "Database error", self)
        if success:
            self.data2 = data2

        # assemble data from both queries into one dict:
        self.cell_line_dic = {}
        self.allele_dic = {}  # contains additional info per local_name not displayed in the table
        self.data = []
        if self.data1:
            self.log.debug("\t{} matching alleles found based on local_name".format(len(self.data1)))
            for row in self.data1:
                self.data.append(row[:-2])
                local_name = row[2]
                gene = row[7]
                target_allele = row[8]
                partner_allele = row[9]
                allele = TargetAllele(gene=gene, target_allele=target_allele, partner_allele=partner_allele)
                self.allele_dic[local_name] = allele
        if self.data2:
            self.log.debug("\t{} matching alleles found based on cell_line_old".format(len(self.data2)))
            for row in self.data2:
                self.data.append(row[:-2])
                local_name = row[2]
                cell_line_old = row[6]
                self.cell_line_dic[local_name] = cell_line_old
                gene = row[7]
                target_allele = row[8]
                partner_allele = row[9]
                allele = TargetAllele(gene=gene, target_allele=target_allele, partner_allele=partner_allele)
                self.allele_dic[local_name] = allele

        self.log.debug("Emitting 'files = {}'".format(len(self.data)))
        self.files.emit(len(self.data))
        self.old_cell_lines.emit(self.cell_line_dic)
        self.additional_info.emit(self.allele_dic)

    def refresh(self, project, addfilter, addfilter2, keep_choices=False):
        self.log.debug("refreshing IPDFileChoiceTable...")
        self.keep_choices = keep_choices
        self.myfilter = " where alleles.project_name = '{}' {} order by project_nr".format(project, addfilter)
        self.myfilter2 = " where alleles.project_name = '{}' {} order by project_nr".format(project, addfilter2)
        self.fill_UI()


class IPDSubmissionForm(CollapsibleDialog):
    """a popup widget to upload alleles of a project to IPD
    """
    IPD_submitted = pyqtSignal()

    def __init__(self, log, mydb, project, settings, parent=None):
        """initiates the IPDSubmissionForm
        """
        self.log = log
        self.log.info("Opening 'IPD Submission' Dialog...")
        self.mydb = mydb
        if check_project_open(project, log, parent=parent):
            self.project = project
        else:
            self.project = ""
        self.settings = settings
        self.label_width = 150
        super().__init__(parent)

        self.resize(1250, 500)
        self.setWindowTitle("Submit alleles to IPD")
        self.setWindowIcon(QIcon(general.favicon))
        self.samples = []
        self.file_dic = {}
        self.add_filter = ""
        self.title = ""
        self.description = ""
        self.imgt_files = {}
        self.submission_successful = False
        self.accepted = False
        self.multis_handled = False
        self.show()
        ok, msg = settings_ok("IPD", self.settings, self.log)
        if not ok:
            QMessageBox.warning(self, "Missing IPD settings", msg)
            self.close()

    def define_sections(self):
        """defining the dialog's sections
        """
        self.define_section1()
        self.define_section2()
        self.define_section3()
        self.define_section4()

    def define_section1(self):
        """defining section 1: choose project & ENA file
        """
        mywidget = QWidget(self)
        layout = QHBoxLayout()
        mywidget.setLayout(layout)

        proj_btn = QueryButton("Choose a (different) existing project",
                               "select project_name from projects where project_status = 'Open' order by project_name desc")
        self.proj_widget = ChoiceSection("Project:", [proj_btn], self.tree, label_width=self.label_width)
        if self.project:
            self.proj_widget.field.setText(self.project)
            proj_btn.change_to_normal(None)

        layout.addWidget(self.proj_widget)

        self.ok_btn1 = ProceedButton("Proceed", [self.proj_widget.field], self.log, 0)
        layout.addWidget(self.ok_btn1)
        self.proj_widget.choice.connect(self.ok_btn1.check_ready)
        self.ok_btn1.proceed.connect(self.proceed_to2)
        self.sections.append(("(1) Choose project:", mywidget))

    def check_first_time_proceed(self):
        """checks if this is this user's first IPD submission;
        if yes, asks for confirmation before proceeding
        """
        if self.settings["modus"] == "staging":
            return True

        self.log.debug("Checking if this is your first IPD submission...")
        query = "select submission_id from ipd_submissions where success = 'yes' limit 1"
        success, data = db_internal.execute_query(query, 1, self.log, "Checking for previous IPD submissions",
                                                  "Database error", self)
        if not success:
            return False
        if data:
            return True
        else:  # first productive submission
            self.log.info("First submission to IPD. Are you sure your settings are ok?")
            msg = "This user has never before created IPD submission files.\n"
            msg += "Before continuing, please check the 'methods' part of your settings:\n"
            msg += "Do these accurately reflect the workflow applied to generate your samples?\n"
            msg += "(See user manual under 'submission_ipd' for details.)\n\n"
            msg += "Are you really sure your settings are ok?"
            reply = QMessageBox.question(self, "First IPD submission",
                                         msg, QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.log.info("\t=> Proceed!")
                return True
            else:
                self.log.info("\t=> I'll go check, wait here.")
                return False

    @pyqtSlot(int)
    def proceed_to2(self, _):
        """proceed to next section
        """
        self.log.debug("proceed_to_2")
        proceed = self.check_first_time_proceed()
        if not proceed:
            self.ok_btn1.setChecked(False)
            return

        self.project = self.proj_widget.field.text()
        proj_open = check_project_open(self.project, self.log, self)
        if not proj_open:
            msg = f"Project {self.project} is currently closed! You cannot create IPD-files from closed projects.\n"
            msg += "To submit alleles of this project to IPD, please open its ProjectView "
            msg += "and click the 'Reopen Project' button!"
            msg += "\nAlternatively, please choose a different project."
            self.log.warning(msg)
            QMessageBox.warning(self, "This project is closed!", msg)
            return

        self.proceed_sections(0, 1)

    def define_section2(self):
        """defining section 1: choose project & ENA file
        """
        mywidget = QWidget(self)
        layout = QGridLayout()
        mywidget.setLayout(layout)

        mypath = self.settings["raw_files_path"]
        ENA_file_btn = FileButton("Upload email attachment from ENA reply", mypath, parent=self)
        self.ENA_file_widget = ChoiceSection("ENA reply file:", [ENA_file_btn], self, label_width=self.label_width)
        if self.settings["modus"] == "debugging":
            self.ENA_file_widget.field.setText(
                r"H:\Projekte\Bioinformatik\Typeloader\example files\both_new\KIR\invalid_ENA.txt")
            ENA_file_btn.change_to_normal()

        layout.addWidget(self.ENA_file_widget, 1, 0)

        befund_file_btn = FileButton("Choose file with pretypings for each sample", mypath, parent=self)
        self.befund_widget = ChoiceSection("Pretyping file:", [befund_file_btn], self, label_width=self.label_width)
        self.befund_widget.setWhatsThis(
            "Choose a file containing a list of previously identified alleles for all loci for each sample")
        if self.settings["modus"] == "debugging":
            self.befund_widget.field.setText(
                r"H:\Projekte\Bioinformatik\Typeloader\example files\both_new\KIR\invalid_pretypings.csv")
            befund_file_btn.change_to_normal()
        layout.addWidget(self.befund_widget, 2, 0)

        self.ok_btn2 = ProceedButton("Proceed", [self.ENA_file_widget.field, self.befund_widget.field], self.log, 0)
        self.proj_widget.choice.connect(self.ok_btn2.check_ready)
        self.befund_widget.choice.connect(self.ok_btn2.check_ready)
        layout.addWidget(self.ok_btn2, 1, 1, 3, 1)
        self.ok_btn2.proceed.connect(self.proceed_to3)
        self.sections.append(("(2) Upload ENA reply file:", mywidget))

        # add hidden button to create fake ENA response & fake pretyping file:
        local_user, self.local_cf = check_local(self.settings, self.log)
        if local_user:  # only visible for LSL users
            self.pretypings_btn = QPushButton("Generate pretyping file")
            self.pretypings_btn.setStyleSheet(general.btn_style_local)
            self.pretypings_btn.clicked.connect(self.get_pretypings)
            layout.addWidget(self.pretypings_btn, 1, 1)

            if check_nonproductive(self.settings):  # only visible for non-productive LSL users
                self.fake_btn = QPushButton("Generate fake input files")
                self.fake_btn.setStyleSheet(general.btn_style_local)
                self.fake_btn.clicked.connect(self.create_fake_input_files)
                layout.addWidget(self.fake_btn, 0, 1)

    @pyqtSlot()
    def create_fake_input_files(self):
        """creates a fake ENA reply file & pretypinsg file
        which can be used to create fake IPD files of any alleles in this project;
        this functionality can be used to create IPD formatted files for alleles 
         that have not been submitted to ENA or have not received an ENA identifier, yet
        """
        self.log.info("Creating fake ENA response file & fake pretypings file...")
        try:
            success, ena_file, pretypings_file = make_fake_ENA_file(self.project, self.log, self.settings, "local_name",
                                                                    self)
        except Exception as E:
            self.log.exception(E)
            QMessageBox.warning(self, "Problem", "Could not generate fake files:\n\n{}".format(repr(E)))
            success = False

        if success:
            self.ENA_file_widget.field.setText(ena_file)
            self.befund_widget.field.setText(pretypings_file)
            self.fake_btn.setStyleSheet(general.btn_style_normal)
            self.ok_btn2.check_ready()
        else:
            QMessageBox.warning(self, ena_file, pretypings_file)

    @pyqtSlot()
    def get_pretypings(self):
        """creates pretypings file from oracle database
        """
        try:
            success, pretypings_file, problems = get_pretypings_from_oracledb(self.project, self.local_cf,
                                                                              self.settings, self.log, self)
        except Exception as E:
            self.log.exception(E)
            QMessageBox.warning(self, "Error while generating pretypings file",
                                "Could not generate the pretypings file:\n\n{}".format(repr(E)))
            success = False
            problems = []
        if success:
            if problems:
                QMessageBox.information(self, "Not all pretypings found",
                                        "Problems occurred when retrieving the following pretypings: \n- {}".format(
                                            "\n- ".join(problems)))

            try:
                suggested_path = os.path.join(self.settings["default_saving_dir"], "pretypings.csv")
                chosen_path = \
                    QFileDialog.getSaveFileName(self, "Download generated pretypings file...", suggested_path)[0]
                self.log.info("Saving generated pretypings file under {}...".format(chosen_path))
                shutil.copy(pretypings_file, chosen_path)
                self.befund_widget.field.setText(chosen_path)
                self.pretypings_btn.setStyleSheet(general.btn_style_normal)
            except Exception as E:
                self.log.exception(E)
                QMessageBox.warning(self, "Error while generating pretypings file",
                                    "Could not save the pretypings file:\n\n{}".format(repr(E)))
                self.pretypings_btn.setChecked(False)
            self.ok_btn2.check_ready()

    def parse_ENA_file(self):
        """parses the ENA reply file,
        stores results and adjusts filter for IPDFileChoiceTable
        """
        self.ENA_reply_file = self.ENA_file_widget.field.text().strip()
        self.ENA_timestamp = general.get_file_creation_date(self.ENA_reply_file, self.settings, self.log)
        self.ENA_id_map, self.ENA_gene_map = MIF.parse_email(self.ENA_reply_file)
        key = "', '".join(sorted(self.ENA_id_map.keys()))
        self.add_filter = " and alleles.local_name in ('{}')".format(key)
        self.add_filter2 = " and alleles.cell_line_old in ('{}')".format(key)

    @pyqtSlot(int)
    def proceed_to3(self, _):
        """proceed to next section
        """
        self.log.debug("proceed_to_3")
        self.parse_ENA_file()
        self.refresh_section3()
        self.proceed_sections(1, 2)

    def refresh_section3(self, keep_choices=False):
        """refreshes data in section3 after project has been changed
        """
        self.log.debug("Refreshing section 3...")
        self.project_info.fill_UI(self.project)
        self.project_files.refresh(self.project, self.add_filter, self.add_filter2, keep_choices=keep_choices)
        if not keep_choices:
            if self.settings["modus"] == "debugging":
                if self.project_files.check_dic:  # if debugging, auto-select first file
                    self.project_files.check_dic[0].setChecked(True)
                    self.project_files.files_chosen.emit(1)

    @pyqtSlot(str, str)
    def catch_project_info(self, title, description):
        """catches title & description emitted by ProjectInfoTable
        """
        self.title = title
        self.description = description

    def define_section3(self):
        """defining section 3: choose alleles
        """
        self.log.debug("Setting up section3 of IPDSubmissionForm...")
        mywidget = QWidget(self)
        layout = QHBoxLayout()
        mywidget.setLayout(layout)
        mywidget.setMinimumHeight(250)
        self.project_info = ProjectInfoTable(self.project, self.log, self)
        self.project_info.setMaximumWidth(350)
        self.project_info.setMinimumWidth(250)
        layout.addWidget(self.project_info)
        self.project_info.project_info.connect(self.catch_project_info)

        self.project_files = IPDFileChoiceTable(self.project, self.log, self)
        layout.addWidget(self.project_files)
        self.project_files.files_chosen.connect(self.project_info.update_files_chosen)
        self.project_files.files.connect(self.project_info.update_files)
        self.project_files.old_cell_lines.connect(self.catch_cell_line)
        self.project_files.additional_info.connect(self.catch_additional_info)

        items = [self.project_info.item(3, 0)]
        self.submit_btn = ProceedButton("Generate IPD files", items, self.log, 1, self)
        self.submit_btn.proceed.connect(self.make_IPD_files)
        self.submit_btn.setMinimumWidth(100)
        layout.addWidget(self.submit_btn)
        self.project_info.updated.connect(self.submit_btn.check_ready)

        self.sections.append(("(3) Choose alleles to submit:", mywidget))

    def get_chosen_samples(self):
        """gets results of file choice in section2,
        stores them in self.samples
        """
        self.samples = []
        for i in self.project_files.check_dic:
            box = self.project_files.check_dic[i]
            if box.checkState():
                sample = self.project_files.item(i, 2).text()
                local_name = self.project_files.item(i, 3).text()
                IPD_nr = self.project_files.item(i, 6).text()
                self.samples.append((sample, local_name, IPD_nr))

    def get_values(self):
        """retrieves values for IPD file generation from GUI
        """
        self.pretypings = self.befund_widget.field.text().strip()
        self.log.debug("pretypings file: {}".format(self.pretypings))
        self.project = self.proj_widget.field.text().strip()
        self.curr_time = time.strftime("%Y%m%d%H%M%S")
        self.subm_id = "IPD_{}".format(self.curr_time)
        return True

    def get_files(self):
        """retrieves ena_file and blast_xml for each chosen sample
        """
        self.file_dic = {}
        for (sample_id_int, local_name, _) in self.samples:
            self.file_dic[local_name] = {}
            query = """select blast_xml, ena_file from files 
            where sample_id_int = '{}' and local_name = '{}'""".format(sample_id_int, local_name)
            success, data = db_internal.execute_query(query, 2, self.log,
                                                      "retrieving sample files", "Database error", self)
            if success:
                self.file_dic[local_name]["blast_xml"] = data[0][0]
                self.file_dic[local_name]["ena_file"] = data[0][1]

    @pyqtSlot(dict)
    def catch_cell_line(self, old_cell_lines):
        """catches mapping between cell_line_old and loca_name 
         for files submitted to ENA under the old cell_line identifier
        """
        if old_cell_lines:
            self.log.debug(
                "Caught mapping between {} old cell_line identifiers and allele names".format(len(old_cell_lines)))
            for local_name in old_cell_lines:
                cell_line_old = old_cell_lines[local_name]
                self.ENA_id_map[local_name] = self.ENA_id_map[cell_line_old]
                self.ENA_gene_map[local_name] = self.ENA_gene_map[cell_line_old]

    @pyqtSlot(dict)
    def catch_additional_info(self, allele_dic):
        """catches mapping between local_name and other info not displayed in the GUI
        for use in befund-part of IPD file
        """
        self.log.debug("Caught mapping between {} allele names and their addiditonal info".format(len(allele_dic)))
        self.allele_dic = allele_dic  # format: {local_name : TargetAllele}

    @pyqtSlot()
    def make_IPD_files(self):
        """tell typeloader to create the IPD file
        """
        self.submit_btn.setChecked(False)
        success = self.get_values()
        if not success:
            return False

        project_dir = os.path.join(self.settings["projects_dir"], self.project)
        mydir = os.path.join(project_dir, "IPD-submissions", self.subm_id)
        os.makedirs(mydir, exist_ok=True)

        try:
            for myfile in [self.ENA_reply_file, self.pretypings]:
                new_path = os.path.join(mydir, os.path.basename(myfile))
                shutil.copy(myfile, new_path)
                myfile = new_path

            self.log.debug("Creating IPD file...")
            self.get_chosen_samples()
            self.get_files()
            results = MIF.write_imgt_files(project_dir, self.samples, self.file_dic, self.allele_dic, self.ENA_id_map,
                                           self.ENA_gene_map, self.pretypings, self.subm_id,
                                           mydir, self.settings, self.log)
            if not results[0]:
                if results[1] == "Invalid pretypings":
                    self.handle_invalid_pretyings(results[2])
                    return False
                elif results[1] == "Multiple novel alleles in target locus":
                    self.handle_multiple_novel_alleles(results[2])
                    return False
                else:
                    if "is currently creating IPD files" in results[1]:
                        mbox = IPDCounterLockedDialog(self, "IPD file creation error", results[1], self.settings,
                                                      self.log)
                        mbox.remove_lock.connect(self.handle_IPDcounter_lock)
                        return False
                    else:
                        print("MIF.write_imgt_files result:")
                        print(results)
                        QMessageBox.warning(self, "IPD file creation error", results[1])
                        return False
            else:
                (self.IPD_file, self.cell_lines, self.customer_dic, resultText, self.imgt_files, success,
                 error) = results
            if error:
                QMessageBox.warning(self, "IPD file creation error",
                                    "An error occurred during the creation of IPD files:\n\n{}".format(repr(error)))
                return False
            if success:
                if not resultText:
                    resultText = "All genes and alleles were resolved"
                self.log.debug("Success: {}".format(resultText))
            else:
                self.log.info("IPD file creation not successful")
                QMessageBox.warning(self, "IPD file creation not successful", "Could not create IPD files!")
                return False

        except Exception as E:
            self.log.error(E)
            self.log.exception(E)
            QMessageBox.warning(self, "IPD file creation error",
                                "An error occured during creation of the IPD files:\n\n{}".format(repr(E)))
            return False

        self.submission_successful = False
        if os.path.exists(self.IPD_file):
            if os.path.getsize(self.IPD_file):
                self.submission_successful = True
        general.play_sound(self.log)

        if self.submission_successful:
            self.log.info("=> Successfully made IPD-file: {}".format(self.IPD_file))
            self.download_btn.setEnabled(True)
            self.download_btn.setStyleSheet(general.btn_style_ready)
            self.ok_btn.setEnabled(True)
            self.submit_btn.setChecked(False)
            self.submit_btn.setStyleSheet(general.btn_style_normal)

            self.save_to_db()
            self.IPD_submitted.emit()
            self.proceed_to4()
            return True
        else:
            self.log.error("No IPD-File created!")
            QMessageBox.warning(self, "IPD file creation error", "Creation of the IPD zip file was not successful")
            return False

    def handle_multiple_novel_alleles(self, problem_dic):
        """if multiple novel alleles were found for the target locus
        """
        self.log.info("Found multiple novel alleles for target locus in {} samples".format(len(problem_dic)))
        self.multi_dialog = BothAllelesNovelDialog(problem_dic, self.settings, self.log)
        self.multi_dialog.updated.connect(self.reattempt_make_IPD_files)
        self.multi_dialog.exec_()
        self.multis_handled = True

    def handle_invalid_pretyings(self, problem_dic):
        """if invalid pretypings were found for the target locus
        """
        self.log.info("Found invalid pretypings in {} samples".format(len(problem_dic)))
        dialog = InvalidPretypingsDialog(problem_dic, self.settings, self.log)
        dialog.ok.connect(self.close)
        dialog.exec_()

    def handle_IPDcounter_lock(self, remove_lock):
        """catches signal from IPDCounterLockedDialog and issues corresponding actions 
        """
        self.log.debug("Signal received: remove IPD lock: {}!".format(remove_lock))
        if remove_lock:
            self.submit_btn.setChecked(False)
            self.log.info("Removing IPD counter lockfile and trying again...")
            lock_file = os.path.join(self.settings["root_path"], "_general", "ipd_nr.lock")
            try:
                os.remove(lock_file)
                self.log.debug("\t=> Success")
            except Exception as E:
                self.log.warning("Could not delete IPD_counter lockfile from {}!".format(lock_file))
                self.log.exception(E)
                msg = "Could not remove IPD lockfile, sorry! Please close the IPD-Submission dialog and try again.\n"
                msg += f"If the problem occurs again, please contact your admin!\n{repr(E)}"
                QMessageBox.warning(self, "Error", msg)
                return
            self.reattempt_make_IPD_files()
        else:
            self.log.info("Will not remove IPD lockfile. Closing IPDSubmissionDialog.")
            self.close()

    def reattempt_make_IPD_files(self):
        self.log.info("Re-attempting IPD file creation...")
        self.refresh_section3(keep_choices=True)
        self.make_IPD_files()

    @pyqtSlot(int)
    def proceed_to4(self):
        """proceed to next section
        """
        text = "Successfully created IPD files for {} alleles:\n".format(len(self.samples))
        for (_, local_name, _) in self.samples:
            text += "\t- {}\n".format(local_name)
        self.textbox.setText(text)
        self.download_btn.setEnabled(True)
        self.proceed_sections(2, 3)

    @pyqtSlot()
    def download_IPD_file(self):
        """download the IPD file
        """
        self.log.debug("Downloading {}...".format(self.IPD_file))
        suggested_path = os.path.join(self.settings["default_saving_dir"], os.path.basename(self.IPD_file))
        chosen_path = QFileDialog.getSaveFileName(self, "Download IPD file...", suggested_path)[0]
        if chosen_path:
            copyfile(self.IPD_file, chosen_path)
        self.download_btn.setStyleSheet(general.btn_style_normal)
        self.close()

    @pyqtSlot()
    def save_to_db(self):
        """updates database with results of ENA submission
        """
        success = False
        if self.submission_successful:
            try:
                self.log.info("Saving changes to db...")
                update_queries = []
                for (sample, local_name, _) in self.samples:
                    # update allele_status for individual alleles:    
                    IPD_submission_nr = self.cell_lines[local_name]
                    update_query = """update alleles set allele_status = 'IPD submitted',
                        ENA_accession_nr = '{}', ENA_acception_date = '{}',
                        IPD_SUBMISSION_ID = '{}', IPD_SUBMISSION_NR = '{}' 
                        where local_name = '{}'""".format(self.ENA_id_map[local_name], self.ENA_timestamp,
                                                          self.subm_id, IPD_submission_nr, local_name)
                    update_queries.append(update_query)

                    # update files table:
                    subm_file = self.imgt_files[IPD_submission_nr]
                    update_files_query = """update files set IPD_submission_file = '{}' where local_name = '{}'
                    """.format(subm_file, local_name)
                    update_queries.append(update_files_query)

                    # update samples table with customer:
                    update_samples_query = """update samples set customer = '{}' where sample_id_int = '{}'
                    """.format(self.customer_dic[sample], sample)
                    update_queries.append(update_samples_query)

                    # copy file to sample folder:
                    src_path = os.path.join(os.path.dirname(self.IPD_file), subm_file)
                    dest_dir = os.path.join(self.settings["projects_dir"], self.project, sample)
                    if not os.path.isdir(dest_dir):
                        self.log.warning("Sample folder {} does not exist! Creating...".format(dest_dir))
                        QMessageBox.warning(self, "Sample path unknown", """Sample directory '{}' does not exist (but it should)!
                        I'm creating it, but please notify your admin!""".format(dest_dir))
                        os.makedirs(dest_dir)
                    dest_path = os.path.join(dest_dir, subm_file)
                    self.log.debug("Copying IPD file to {}...".format(dest_path))
                    try:
                        shutil.copy(src_path, dest_path)
                    except Exception as E:
                        self.log.warning("Could not copy file {} to {}".format(subm_file, dest_dir))
                        self.log.exception(E)
                        QMessageBox.warning(self, "File copy error",
                                            "Could not copy file '{}' to its sample-folder '{}'!".format(
                                                os.path.basename(subm_file), dest_dir))

                # update IPD_submissions table:
                today = time.strftime("%Y-%m-%d")
                query2 = """insert into IPD_submissions 
                (SUBMISSION_ID, NR_ALLELES, TIMESTAMP_SENT, SUCCESS) values
                ('{}', {}, '{}', 'yes')""".format(self.subm_id, len(self.cell_lines), today)
                update_queries.append(query2)

                success = db_internal.execute_transaction(update_queries, self.mydb, self.log,
                                                          "trying to save this submission to the database",
                                                          "Database error", self)
                if success:
                    self.IPD_submitted.emit()
                    self.log.info("=> Database updated successfully")

                else:
                    self.log.info("=> Database NOT updated!")
            except Exception as E:
                QMessageBox.warning(self, "Database error",
                                    "Could not save this IPD submission to the database (see below). Rolling back...\n\n{}".format(
                                        repr(E)))
                self.log.error(E)
                self.log.exception(E)

    def define_section4(self):
        """defining section 4: download IPD file
        """
        mywidget = QWidget(self)
        layout = QGridLayout()
        mywidget.setLayout(layout)

        self.textbox = QTextEdit(self)
        self.textbox.setMinimumHeight(200)

        layout.addWidget(self.textbox, 0, 0, 2, 1)

        self.download_btn = QPushButton("Download zipped IPD files", self)
        self.download_btn.setEnabled(False)
        self.download_btn.clicked.connect(self.download_IPD_file)
        layout.addWidget(self.download_btn, 0, 1)

        self.ok_btn = QPushButton("Close", self)
        self.ok_btn.setEnabled(False)
        self.ok_btn.clicked.connect(self.close)
        layout.addWidget(self.ok_btn, 1, 1)

        self.sections.append(("(4) Check results:", mywidget))


pass


# ===========================================================
# functions:

def log_uncaught_exceptions(cls, exception, tb):
    """reimplementation of sys.excepthook;
    catches uncaught exceptions, logs them and exits the app
    """
    import traceback
    from PyQt5.QtCore import QCoreApplication
    log.critical('{0}: {1}'.format(cls, exception))
    log.exception(msg="Uncaught Exception", exc_info=(cls, exception, tb))
    # TODO: (future) maybe find a way to display the traceback only once, both in console and logfile?
    sys.__excepthook__(cls, exception, traceback)
    QCoreApplication.exit(1)


pass
# ===========================================================
# main:

if __name__ == '__main__':
    from typeloader_GUI import create_connection, close_connection
    import GUI_login

    sys.excepthook = log_uncaught_exceptions
    log = general.start_log(level="DEBUG")
    log.info("<Start {}>".format(os.path.basename(__file__)))
    settings_dic = GUI_login.get_settings("admin", log)
    mydb = create_connection(log, settings_dic["db_file"])

    project = "20190628_ADMIN_mixed_ENA-test"
    app = QApplication(sys.argv)

    #     ex = BothAllelesNovelDialog(allele_dic, settings_dic, log)
    ex = IPDSubmissionForm(log, mydb, project, settings_dic)

    ex.show()

    result = app.exec_()
    close_connection(log, mydb)
    log.info("<End>")
    sys.exit(result)

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import (QDialog, QFileDialog, QFormLayout, QVBoxLayout,
                             QLabel, QApplication)
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtGui import QIcon
from PyQt5.Qt import QPushButton, QMessageBox

import sys, os, shutil
from shutil import copyfile

import general
from GUI_forms import FileButton, ProceedButton, ChoiceSection


# ===========================================================
# classes:


class ExampleFileDialog(QDialog):
    """a dialog to download example files
    """

    def __init__(self, settings, log, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.log = log
        self.setWindowTitle("Download example files")
        self.setWindowIcon(QIcon(general.favicon))
        self.resize(200, 50)
        self.init_UI()
        self.setModal(True)
        self.show()

    def init_UI(self):
        """establish and fill the UI
        """
        layout = QFormLayout(self)
        self.setLayout(layout)
        self.btn_dic = {}

        # sequence files:
        seq_lbl = QLabel("Example sequence files:")
        seq_lbl.setStyleSheet(general.label_style_2nd)
        layout.addRow(seq_lbl)

        seq_HLA_btn = QPushButton("Download!", self)
        self.btn_dic[seq_HLA_btn] = ("HLA-A", "HLA-A_01-01-01-01.fa")
        seq_HLA_btn.clicked.connect(self.download_file)
        HLA_msg = "Click here to download an example fasta file for an existing HLA-A allele. It can be used as Input for New Sequence."
        seq_HLA_btn.setWhatsThis(HLA_msg)
        layout.addRow(QLabel("HLA-A example:"), seq_HLA_btn)

        seq_KIR1_btn = QPushButton("Download!", self)
        self.btn_dic[seq_KIR1_btn] = ("KIR2DL1", "KIR2DL1_0020101.fa")
        seq_KIR1_btn.clicked.connect(self.download_file)
        seq_KIR1_btn.setWhatsThis(
            "This is an example fasta file for an existing KIR2DL1 allele. It can be used as Input for New Sequence.")
        layout.addRow(QLabel("KIR example 1 (KIR2DL1 contains a pseudoexon):"), seq_KIR1_btn)

        seq_KIR2_btn = QPushButton("Download!", self)
        self.btn_dic[seq_KIR2_btn] = ("KIR2DL4", "KIR2DL4_0010201.fa")
        seq_KIR2_btn.clicked.connect(self.download_file)
        seq_KIR2_btn.setWhatsThis(
            "This is an example fasta file for an existing KIR2DL4 allele. It can be used as Input for New Sequence.")
        layout.addRow(QLabel("KIR example 2 (KIR2DL4 contains a deleted exon):"), seq_KIR2_btn)

        seq_MICA_btn = QPushButton("Download!", self)
        self.btn_dic[seq_MICA_btn] = ("MICA", "MICA_002_01.fa")
        seq_MICA_btn.clicked.connect(self.download_file)
        seq_MICA_btn.setWhatsThis(
            "This is an example fasta file for an existing MICA allele. It can be used as Input for New Sequence.")
        layout.addRow(QLabel("MICA example:"), seq_MICA_btn)

        # IPD submission input files:
        ipd_lbl = QLabel("Example input files for IPD submission:")
        ipd_lbl.setStyleSheet(general.label_style_2nd)
        layout.addRow(ipd_lbl)

        ENA_reply_btn = QPushButton("Download!", self)
        self.btn_dic[ENA_reply_btn] = ("ENA reply", "fake_ENA_reply.txt")
        ENA_reply_btn.clicked.connect(self.download_file)
        ENA_reply_btn.setWhatsThis(
            "This file is a truncated version of the file sent by ENA after ID assignment. It can be used as input for IPD file creation of the example sequences.")
        layout.addRow(QLabel("ENA reply file:"), ENA_reply_btn)

        pretypings_btn = QPushButton("Download!", self)
        self.btn_dic[pretypings_btn] = ("pretypings", "pretypings_example.csv")
        pretypings_btn.clicked.connect(self.download_file)
        pretypings_btn.setWhatsThis(
            "This file contains a list of previously identified alleles for all loci for each sample to be submitted to IPD. It can be used as input for IPD file creation of the example sequences.")
        layout.addRow(QLabel("Pretypings file:"), pretypings_btn)

    @pyqtSlot()
    def download_file(self):
        """downloads the example file corresponding to the sending button from TypeLoader
        """
        (designator, filename) = self.btn_dic[self.sender()]
        self.log.info("Downloading example {} file...".format(designator))
        myfile = os.path.join("sample_files", filename)
        if not os.path.exists(myfile):
            myfile = os.path.join(self.settings["root_path"], "_general", "sample_files", filename)
        if os.path.exists(myfile):
            suggested_path = os.path.join(self.settings["default_saving_dir"], myfile)
            chosen_path = \
                QFileDialog.getSaveFileName(self, "Download example {} file...".format(designator), suggested_path)[0]
            if chosen_path:
                try:
                    copyfile(myfile, chosen_path)
                    self.log.info("\tDownload successful!")
                except Exception as E:
                    self.log.error("\t=> Download failed!")
                    self.log.exception(E)
                    QMessageBox.warning(self, "Dowload failed",
                                        "Sorry, I could not download the file you requested:\n\n{}".format(repr(E)))
        else:
            self.log.error("File not found: {}".format(myfile))
            QMessageBox.warning(self, "File not found",
                                "Sorry, I could not find the file you requested: \n{}".format(myfile))
            self.log.info("\tDownload aborted. :(")


class LogFileDialog(QDialog):
    """a dialog to download the current log file
    """

    def __init__(self, settings, log, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.log = log
        self.parent = parent
        self.warning = ""
        self.log_dir = os.path.join(settings["recovery_dir"])
        self.log.info("Opened LogFileDialog")

        self.setWindowTitle("Download log file")
        self.setWindowIcon(QIcon(general.favicon))
        self.resize(300, 100)
        self.init_UI()
        self.setModal(True)
        self.show()

    def init_UI(self):
        """establish and fill the UI
        """
        layout = QVBoxLayout(self)
        self.setLayout(layout)

        msg = "If you wish to show the TypeLoader developers details about a current problem, "
        msg += "you can download a log file here.\n"
        layout.addWidget(QLabel(msg))

        layout.addWidget(QLabel("Use any file that ends with .log.\n"))

        msg2 = "All logfiles are named with the timestamp of the start of the respective TypeLoader session.\n"
        msg2 += "Usually, you want the latest one (so the file at the bottom of the list).\n"
        layout.addWidget(QLabel(msg2))

        msg3 = "Before doing this, it is very helpful if you close TypeLoader, reopen it, "
        msg3 += "and perform only the steps necessary to reproduce your problem!\n"
        layout.addWidget(QLabel(msg3))

        self.choice_btn = FileButton("Choose log file", default_path=self.log_dir, parent=self, log=self.log)
        self.file_widget = ChoiceSection("Choose a .log file:", [self.choice_btn], self)
        self.file_widget.choice.connect(self.get_file)
        msg = "Click here to select a log file to show the TypeLoader developers details about your latest issue."
        self.file_widget.setWhatsThis(msg)
        layout.addWidget(self.file_widget)

        self.dld_btn = ProceedButton("Download log file!", [self.file_widget.field], self.log, parent=self)
        self.dld_btn.clicked.connect(self.download_file)
        self.file_widget.field.textChanged.connect(self.dld_btn.check_ready)
        layout.addWidget(self.dld_btn)

    @pyqtSlot(str)
    def get_file(self, path, testing=False):
        """catches path from self.file_widget,
        stores it as self.file
        """
        if os.path.dirname(os.path.abspath(path)) == os.path.abspath(self.log_dir):
            self.file = path
            self.log.debug("File chosen for download: {}".format(path))
            if not self.file.endswith(".log"):
                msg = "This is not a log file! Please choose a file that ends with .log!"
                if self.parent:
                    QMessageBox.warning(self, "Wrong file type", msg)
                    return
                else:
                    return msg
            self.dld_btn.setEnabled(True)
        else:  # file not allowed (outside of scope)
            msg = "This file is not a logfile of the user you started this dialog from!"
            if self.parent:
                QMessageBox.warning(self, "Forbidden file", msg)
                self.dld_btn.setEnabled(False)
                self.dld_btn.setStyleSheet(general.btn_style_normal)
                return
            else:
                return msg

    @pyqtSlot()
    def download_file(self, chosen_path="", suppress_messagebox=False):
        """opens QFileDialog, saves file in chosen location
        """
        if self.file:
            self.log.debug("Downloading logfile from {}...".format(self.file))
            suggested_path = os.path.join(self.settings["default_saving_dir"], os.path.basename(self.file))
        if not chosen_path:
            chosen_path = QFileDialog.getSaveFileName(self, "Download file...", suggested_path)[0]
        if chosen_path:
            self.warning = "Before sending this file to anyone, please open it in a text editor and "
            self.warning += "delete or rephrase anything that looks confidential.\n\n"
            self.warning += "The TypeLoader developers will NOT be held accountable if you breach any confidentiality "
            self.warning += "issues by using this feature!"

            self.log.info(self.warning.replace("\n\n", "\n"))

            shutil.copyfile(self.file, chosen_path)
            self.dld_btn.setChecked(False)

            self.log.info("\t=> logfile downloaded successfully!")

            if not suppress_messagebox:
                QMessageBox.information(self, "Check for confidential info before sending!", self.warning)


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


def main():
    import GUI_login
    log = general.start_log(level="DEBUG")
    log.info("<Start {}>".format(os.path.basename(__file__)))
    settings_dic = GUI_login.get_settings("admin", log)
    app = QApplication(sys.argv)
    sys.excepthook = log_uncaught_exceptions

    ex = LogFileDialog(settings_dic, log)
    ex.show()
    result = app.exec_()

    log.info("<End>")
    sys.exit(result)


if __name__ == '__main__':
    main()

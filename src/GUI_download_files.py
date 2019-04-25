#!/usr/bin/python3
# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import (QDialog, QFileDialog, QFormLayout,
                             QLabel, QApplication)
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtGui import QIcon

import sys, os
from shutil import copyfile

import general

from __init__ import __version__
from PyQt5.Qt import QPushButton


#===========================================================
# classes:

class ExampleFileDialog(QDialog):
    """a dialog to download example files
    """
    def __init__(self, settings, log, parent = None):
        super().__init__(parent)
        self.settings = settings
        self.log = log
        self.setWindowTitle("Download example files")
        self.setWindowIcon(QIcon(general.favicon))
        self.resize(200,50)
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
        seq_KIR1_btn.setWhatsThis("This is an example fasta file for an existing KIR2DL1 allele. It can be used as Input for New Sequence.")
        layout.addRow(QLabel("KIR example 1 (KIR2DL1 contains a pseudoexon):"), seq_KIR1_btn)
        
        seq_KIR2_btn = QPushButton("Download!", self)
        self.btn_dic[seq_KIR2_btn] = ("KIR2DL4", "KIR2DL4_0010201.fa")
        seq_KIR2_btn.clicked.connect(self.download_file)
        seq_KIR2_btn.setWhatsThis("This is an example fasta file for an existing KIR2DL4 allele. It can be used as Input for New Sequence.")
        layout.addRow(QLabel("KIR example 2 (KIR2DL4 contains a deleted exon):"), seq_KIR2_btn)
        
        seq_MICA_btn = QPushButton("Download!", self)
        self.btn_dic[seq_MICA_btn] = ("MICA", "MICA_001.fa")
        seq_MICA_btn.clicked.connect(self.download_file)
        seq_MICA_btn.setWhatsThis("This is an example fasta file for an existing MICA allele. It can be used as Input for New Sequence.")
        layout.addRow(QLabel("MICA example:"), seq_MICA_btn)
        
        # IPD submission input files:
        ipd_lbl = QLabel("Example input files for IPD submission:")
        ipd_lbl.setStyleSheet(general.label_style_2nd)
        layout.addRow(ipd_lbl)
        
        ENA_reply_btn = QPushButton("Download!", self)
        self.btn_dic[ENA_reply_btn] = ("ENA reply", "fake_ENA_reply.txt")
        ENA_reply_btn.clicked.connect(self.download_file)
        ENA_reply_btn.setWhatsThis("This file is a truncated version of the file sent by ENA after ID assignment. It can be used as input for IPD file creation of the example sequences.")
        layout.addRow(QLabel("ENA reply file:"), ENA_reply_btn)
        
        pretypings_btn = QPushButton("Download!", self)
        self.btn_dic[pretypings_btn] = ("pretypings", "pretypings_example.csv")
        pretypings_btn.clicked.connect(self.download_file)
        pretypings_btn.setWhatsThis("This file contains a list of previously identified alleles for all loci for each sample to be submitted to IPD. It can be used as input for IPD file creation of the example sequences.")
        layout.addRow(QLabel("Pretypings file:"), pretypings_btn)
        
    @pyqtSlot()
    def download_file(self):
        """downloads the example file corresponding to the sending button from TypeLoader
        """
        (designator, filename) = self.btn_dic[self.sender()]
        self.log.info("Downloading example {} file...".format(designator))
        myfile = os.path.join("sample_files", filename)
        suggested_path = os.path.join(self.settings["default_saving_dir"], myfile)
        chosen_path = QFileDialog.getSaveFileName(self, "Download example {} file...".format(designator), suggested_path)[0]
        if chosen_path:
            copyfile(myfile, chosen_path)
            self.log.info("\tDownload successful!")
pass
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
    
pass    
#===========================================================
# main:


def main():
    import GUI_login
    log = general.start_log(level="DEBUG")
    log.info("<Start {} V{}>".format(os.path.basename(__file__), __version__))
    settings_dic = GUI_login.get_settings("admin", log)
    app = QApplication(sys.argv)
    sys.excepthook = log_uncaught_exceptions
    
    ex = ExampleFileDialog(settings_dic, log)
    ex.show()
    result = app.exec_()
    
    log.info("<End>")
    sys.exit(result)


if __name__ == '__main__':
    main()
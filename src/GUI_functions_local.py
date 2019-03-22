#!/usr/bin/env python3
# -*- coding: cp1252 -*-
'''
Created on 11.03.2019

GUI_functions_local.py

contains TypeLoader functionality designed especially for use at DKMS Life Science Lab

@author: Bianca Schoene
'''

# import modules:
import os
from configparser import ConfigParser
from PyQt5.QtWidgets import QMessageBox

import db_internal, general, typeloader_functions, GUI_login
from typeloader_core import enaemailparser

#===========================================================
# parameters:

local_config_file = "config_local.ini" 

#===========================================================
# functions:

def read_local_settings(settings, log):
    """reads settings from local config file,
    returns ConfigParser object
    """
    global local_config_file
    if settings["modus"] == "staging":
        local_config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), local_config_file)
    log.info("Reading local settings from {}...".format(local_config_file))
    cf = ConfigParser()
    cf.read(local_config_file)
    return cf


def check_local(settings, log):
    """returns True if this is a DKMS user,
    else returns False 
    """
    permission = False
    local_cf = read_local_settings(settings, log)
    if settings["lab_of_origin"] == local_cf.get("Local", "company_name"):
        permission = True
    return permission


def check_nonproductive(settings):
    """returns True if this user is not a productive user,
    else returns False
    """
    permission = False
    if settings["modus"] != "productive":
        permission = True
    return permission


def make_fake_ENA_file(project, log, settings, basis = "local_name", parent = None):
    """creates a pseudo-ENA reply file with random ENA accession IDs and a pseudo pretypings file,
    which can be used to create fake-IPD files before ENA has assigned official accession numbers
    """
    log.info("Finding alleles of project {}...".format(project))
    query = "select distinct sample_id_int, cell_line_old, local_name, gene, target_allele, partner_allele from alleles where project_name = '{}'".format(project)
    success, data = db_internal.execute_query(query, 6, log, "getting samples from database", "DB error", parent)
    if not success:
        return False, None, None
    
    # write fake ENA file:
    log.info("Writing fake ENA file...")
    fake_file_ena = os.path.join(settings["login_dir"], "temp", "fake_ENA_reply.txt")
    data2 = []
    with open(fake_file_ena, "w") as g:
        for [sample_id_int, cell_line_old, local_name, mygene, target_allele, partner_allele] in data:
            if basis == "local_name":
                cell_line = local_name
            elif basis == "old cell_line":
                cell_line = cell_line_old
            log.debug("\t{}...".format(cell_line))
            data2.append((sample_id_int, cell_line, mygene, target_allele, partner_allele)) # needed for pretyping file
            fake_ID = typeloader_functions.id_generator(size=8)
            gene_type = "gene"
            if mygene in settings["pseudogenes"].split("|"):
                gene_type = "pseudogene"
            g.write("ID   {}; SV 1; linear; genomic DNA; STD; XXX; 35 BP.\nXX\n".format(fake_ID))
            g.write("FH   Key             Location/Qualifiers\nFT   source          1..35\n")
            g.write('FT                   /cell_line="{}"\n'.format(cell_line))
            g.write("FT   CDS             join(1..35)\n")
            g.write('FT                   /{}="{}"\nXX\n'.format(gene_type, mygene))
            g.write("SQ   Sequence 35 BP; 1267 A; 928 C; 1161 G; 880 T; 0 other;\n")
            g.write("     gtgacccact gcttgtttct gtcacaggtg aggaa                                35\n//\n")
    
    # write fake pretyping file:
    log.info("Writing fake pretyping-file...")
    fake_file_befunde = os.path.join(settings["login_dir"], "temp", "fake_befunde.csv")
    columns = ['A1', 'A2', 'B1', 'B2', 'C1', 'C2', 'DR1', 'DR2', 'DQ1', 'DQ2', 'DP1', 'DP2', 'KIR2DL1-1', 'KIR2DL1-2', 'KIR2DL1-3', 'KIR2DL1-4', 'KIR2DL2-1', 'KIR2DL2-2', 'KIR2DL2-3', 'KIR2DL2-4', 'KIR2DL3-1', 'KIR2DL3-2', 'KIR2DL3-3', 'KIR2DL3-4', 'KIR2DL4-1', 'KIR2DL4-2', 'KIR2DL4-3', 'KIR2DL4-4', 'KIR2DL5-1', 'KIR2DL5-2', 'KIR2DL5-3', 'KIR2DL5-4', 'KIR2DP1-1', 'KIR2DP1-2', 'KIR2DP1-3', 'KIR2DP1-4', 'KIR2DS1-1', 'KIR2DS1-2', 'KIR2DS1-3', 'KIR2DS1-4', 'KIR2DS2-1', 'KIR2DS2-2', 'KIR2DS2-3', 'KIR2DS2-4', 'KIR2DS3-1', 'KIR2DS3-2', 'KIR2DS3-3', 'KIR2DS3-4', 'KIR2DS4-1', 'KIR2DS4-2', 'KIR2DS4-3', 'KIR2DS4-4', 'KIR2DS5-1', 'KIR2DS5-2', 'KIR2DS5-3', 'KIR2DS5-4', 'KIR3DL1-1', 'KIR3DL1-2', 'KIR3DL1-3', 'KIR3DL1-4', 'KIR3DL2-1', 'KIR3DL2-2', 'KIR3DL2-3', 'KIR3DL2-4', 'KIR3DL3-1', 'KIR3DL3-2', 'KIR3DL3-3', 'KIR3DL3-4', 'KIR3DP1-1', 'KIR3DP1-2', 'KIR3DP1-3', 'KIR3DP1-4', 'KIR3DS1-1', 'KIR3DS1-2', 'KIR3DS1-3', 'KIR3DS1-4', 'MICA-1', 'MICA-2', 'MICB-1', 'MICB-2']
    
    gene_dic = {"HLA-A": ['A1', 'A2'], 
                "HLA-B": ['B1', 'B2'],
                "HLA-C": ['C1', 'C2'],
                "HLA-DPB1": ['DP1', 'DP2'], 
                "HLA-DQB1": ['DQ1', 'DQ2'],
                "HLA-DRB1": ['DR1', 'DR2'],
                "MICA": ['MICA-1', 'MICA-2'],
                "MICB": ['MICB-1', 'MICB-2']}
    for g in ['KIR2DL1', 'KIR2DL2', 'KIR2DL3', 'KIR2DL4', 'KIR2DL5',
              'KIR2DP1',
              'KIR2DS1', 'KIR2DS2', 'KIR2DS3', 'KIR2DS4', 'KIR2DS5',
              'KIR3DL1', 'KIR3DL2', 'KIR3DL3',
              'KIR3DP1', 'KIR3DS1']:
        l = []
        for i in range(1,5):
            l.append('{}-{}'.format(g, i))
        gene_dic[g] = l
    
    default_dic = {}
    for col in columns:
        if col.startswith("KIR"):
            default_dic[col] = "001"
        else:
            default_dic[col] = "01:01"
    
    with open(fake_file_befunde, "w") as g:
        header = "INTAUF_ID,Spendernr,Auftraggeber,{}\n".format(",".join(columns))
        g.write(header)
        
        for (sample_id_int, cell_line, mygene, target_allele, partner_allele) in data2:
            befunde = default_dic
            for i, col in enumerate(gene_dic[mygene]):
                if i == 0:
                    befunde[col] = target_allele.split("*")[1]
                elif i == 1:
                    if partner_allele:
                        befunde[col] = partner_allele.split("*")[1]
                else:
                    befunde[col] = ""
            myline = "{},{},DKMS,".format(sample_id_int, cell_line)
            pretypings = [befunde[col] for col in columns]
            myline += ",".join(pretypings) + "\n"
            g.write(myline)
            print(myline)
            
     
#     # check generated ENA file: (This will set the alleles' status to "IPD submitted"!)
#     log.info("Checking created ENA file...")
#     (info_dict, gene_dict) = enaemailparser.parse_embl_response(fake_file_ena)
#      
#     if len(info_dict.keys()) == len(gene_dict) == len(data):
#         log.info("Success!")
#     else:
#         msg = "Numbers are not matching up. Something's wrong!"
#         log.warning(msg)
#         if parent:
#             QMessageBox.warning(parent, "Error while generating fake ENA files", msg)
    
    log.debug("Fake ENA file: {}".format(fake_file_ena))
    log.debug("Fake Befunde file: {}".format(fake_file_befunde))
    return True, fake_file_ena, fake_file_befunde
            

def main(log):
    user = "admin"
    project = "20190321_ADMIN_MIC_1"
    
    settings = GUI_login.get_settings(user, log)
    
    from typeloader_GUI import create_connection, close_connection
    db_file = settings["db_file"]
    mydb = create_connection(log, db_file)
    
    try:
        make_fake_ENA_file(project, log, settings, basis = "local_name")
    except Exception as E:
        log.exception(E)
    
    close_connection(log, mydb)
    

if __name__ == '__main__':
    log = general.start_log(level="DEBUG")
    log.info("<Start>")
    main(log)
    log.info("<End>")

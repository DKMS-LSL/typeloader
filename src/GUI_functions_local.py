#!/usr/bin/env python3
# -*- coding: cp1252 -*-
'''
Created on 11.03.2019

GUI_functions_local.py

contains TypeLoader functionality designed especially for use at DKMS Life Science Lab

@author: Bianca Schoene
'''

# import modules:
import os, copy
from configparser import ConfigParser

import db_internal, general, typeloader_functions, GUI_login

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
    kir_contained = False
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
            if mygene.startswith("KIR"):
                kir_contained = True
    
    # write fake pretyping file:
    log.info("Writing fake pretyping-file...")
    fake_file_befunde = os.path.join(settings["login_dir"], "temp", "fake_befunde.csv")
    columns = ["HLA-A_1", "HLA-A_2", "HLA-B_1", "HLA-B_2", "HLA-C_1", "HLA-C_2", "HLA-DRB1_1", 
               "HLA-DRB1_2", "HLA-DQB1_1", "HLA-DQB1_2", "HLA-DPB1_1", "HLA-DPB1_2", 
               "HLA-E_1", "HLA-E_2", "AB0", "RHD", "CCR5_1", "CCR5_2", "KIR", "MICA", "MICB", "CMV"]
    
    gene_dic = {}
    for g in ["HLA-A", "HLA-B", "HLA-C", "HLA-DRB1", "HLA-DQB1", "HLA-DPB1", "HLA-E", "CCR5"]:
        gene_dic[g] = ["{}_1".format(g), "{}_2".format(g)]
    for g in ["AB0", "RHD", "MICA", "MICB", "CMV"]:
        gene_dic[g] = [g]
    kir_columns = []
    for g in ['KIR2DL1', 'KIR2DL2', 'KIR2DL3', 'KIR2DL4', 'KIR2DL5',
              'KIR2DP1',
              'KIR2DS1', 'KIR2DS2', 'KIR2DS3', 'KIR2DS4', 'KIR2DS5',
              'KIR3DL1', 'KIR3DL2', 'KIR3DL3',
              'KIR3DP1', 'KIR3DS1']:
        l = []
        for i in range(1,5):
            l.append('{}-{}'.format(g, i))
        gene_dic[g] = l
        kir_columns += l
    
    default_dic = {}
    if kir_contained:
        columns += kir_columns
    for col in columns:
        if col.startswith("HLA"):
            default_dic[col] = "01:01"
        elif col.startswith("KIR"):
            if col[-1] in ["1", "2"]:
                default_dic[col] = "001"
            else:
                default_dic[col] = ""
        elif col == "AB0":
            default_dic[col] = "A"
        elif col == "RHD":
            default_dic[col] = "+"
        elif col.startswith("CCR5"):
            default_dic[col] = "WT"
        elif col.startswith("CMV"):
            default_dic[col] = "+"
        elif col == "MICA":
            default_dic[col] = "A001+A001"
        elif col == "MICB":
            default_dic[col] = "B001+B001"
            
    
    with open(fake_file_befunde, "w") as g:
        header = "sample_ID,internal_ID,client,{}\n".format(",".join(columns))
        g.write(header)
        
        for (sample_id_int, cell_line, mygene, target_allele, partner_allele) in data2:
            befunde = copy.copy(default_dic)
            # overwrite pretyping of target allele:
            if len(gene_dic[mygene]) == 1:
                if mygene.startswith("MIC"):
                    if not partner_allele:
                        partner_allele = "{}001".format(mygene[-1])
                    befunde[mygene] = "{}+{}".format(target_allele, partner_allele).replace("MICA*","A")
                else:
                    print("Cannot generate sensible fake pretyping: {} should have 2 columns!".format(mygene))
            else:
                for i, col in enumerate(gene_dic[mygene]):
                    if i == 0:
                        befunde[col] = target_allele.split("*")[1]
                    elif i == 1:
                        if partner_allele:
                            befunde[col] = partner_allele.split("*")[1]
                    else:
                        befunde[col] = ""
            # generate row for pretyping file:
            myline = "{},{},DKMS,".format(cell_line, sample_id_int)
            pretypings = [befunde[col] for col in columns]
            myline += ",".join(pretypings) + "\n"
            g.write(myline)
            
     
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
    project = "20190415_ADMIN_MIC_2"
    
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

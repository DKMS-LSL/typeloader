#!/usr/bin/env python3
# -*- coding: cp1252 -*-
'''
Created on 16.05.2019

db_external.py

functionality to interact with databases outside of TypeLoader

@author: Bianca Schoene
'''

# import modules:

import sys, os, csv
import cx_Oracle
import general

#===========================================================
# parameters:

from __init__ import __version__

#===========================================================
# classes:

class DB_scheme():
    """database scheme object,
    contains data necessary to connect to it
    """
    def __init__(self, name, db, host, user, pwd):
        self.name = name
        self.db = db
        self.host = host
        self.user = user
        self.pwd = pwd
    
    def __repr__(self):
        return self.name

pass
#===========================================================
# general db functions:
 
def open_connection(scheme, log):
    """opens an oracle connection to the specified database scheme,
    returns a connection object and cursor
    """
    log.info("Opening database connection to {}...".format(scheme.name))
    try:
        conn_string = r'%s/%s@%s/%s' %(scheme.user, scheme.pwd, scheme.host, scheme.db)
        conn = cx_Oracle.connect(conn_string)
        cursor = conn.cursor()
    except Exception as E:
        log.error("\t=> Could not connect!")
        log.exception(E)
        return None, None
    
    log.info("\t=> Success!")
    return conn, cursor


def close_connection(conn, cursor, log):
    """closes cursor object and conn object of a connection
    """
    log.info("Closing database connection...")
    try:
        cursor.close()
    except:
        log.debug("\tCould not close cursor!")
    try:
        conn.close()
    except:
        log.debug("\tCould not close connection!")
    log.info("\t=> db connection closed")


def query_database(scheme, query, log, return_columns = False):
    """(for SELECT statements)
    queries a database scheme,
    returns list of all data (cursor.fetchall()) and list of column names
    """
    log.info("Querying database...")
    conn, cursor = open_connection(scheme, log)
    cursor.execute(query)

    data = None
    columns = []
    try:
        if return_columns:# generate list of column names:
            desc = cursor.description
            columns = [x[0] for x in desc]
        # get data:
        data = cursor.fetchall()
    except Exception as E:
        close_connection(conn, cursor, log)
        log.error("\t=> Query failed!")
        log.exception(E)
        log.info(query)

    close_connection(conn, cursor, log)
    if return_columns:
        return data, columns
    else:
        return data
    

def query_many(scheme, query, items, log, return_columns = False):
    """(for SELECT statements with multiple datasets)
    queries a database scheme,
    returns list of all data (cursor.fetchall()) and list of column names;
    items needs to be a list of lists or tuple of lists
    """
    conn, cursor = open_connection(scheme, log)
    log.info("Querying database for {} items...".format(len(items)))
    try:
        cursor.prepare(query)
        final_data = []

        # get data:
        for data_set in items:
            cursor.execute(None, data_set)
            data = cursor.fetchall()
            final_data.append(data)
    
        # generate list of column names:
        desc = cursor.description
        columns = [x[0] for x in desc]
    except Exception as E:
        close_connection(conn, cursor, log)
        log.error("\t=> Query failed!")
        log.exception(E)
        log.info(query)
        sys.exit()
    
    log.info("\t=> Success!")
    close_connection(conn, cursor, log)
    if return_columns:
        return final_data, columns
    else:
        return final_data


def call_procedure(procname: str,
                   paramlist: list,
                   num_output_values: int,
                   paramlist2: list,
                   cursor: cx_Oracle.CURSOR,
                   log
                   ) -> tuple:
    """
    Call a stored procedure procname via the given cursor.

    :param procname: name of the oracle procedure to be called
    :param paramlist: list of parameters to be passed before the return values
    :param num_output_values: number of expected return values (all are expected as STRINGS!)
    :param paramlist2: list of parameters to be passed after the return values
    :param cursor: cursor to an open oracle connection
    :param log: logger instance

    :return: tuple (bool for success, return value)
    """
    log.debug(f"Calling procedure {procname}...")
    success = False

    try:
        res_variables = []  # list of oracle variables for each return value
        ret_values = []  # list of return values
        for i in range(num_output_values):
            res = cursor.var(str)
            paramlist.append(res)
            res_variables.append(res)
        paramlist += paramlist2
        cursor.callproc(procname, paramlist)

        for res in res_variables:
            value = res.getvalue()
            ret_values.append(value)

        log.debug("\tSuccessfully called stored procedure!")
        success = True
        return success, ret_values

    except Exception as E:
        log.error(f"The following exception occurred when executing {procname}: ")
        log.error(E)
        log.exception(E)
        conn = cursor.connection
        cursor.close()
        conn.close()
        return success, None

pass
#===========================================================
# specialized TypeLoader functions:


def split_GL_string(GL_string):
    """splits GL-string into alleles;
    if it becomes too complicated, reduce to POS
    """
    if "|" in GL_string: # pretyping contains phasing
        return [GL_string] # put everything into first field
    else:
        alleles = GL_string.split("+")
        if len(alleles) > 4: # GCN > 4 is probably incorrect
            return ["POS"]
        else:
            return alleles
    

def split_2DL5AB(GL, cursor, log):
    """
    splits the KIR2DL5 GL-string into 2 separate GL strings for 2DL5A and 2DL5B

    :param GL: GL-string for KIR2DL5, combining both A and B
    :param cursor: cursor to a connection to the nextype archive
    :param log: logger instance
    """
    log.info("Splitting 2DL5-alleles...")

    proc_name = "GL_STRINGS_MGMT.SPLIT_GL_STRING_2DL5@ngsa"
    proc_params = [GL]
    proc_params2 = [2, 'KIR', 'J', 'J', '2DL5', 'J', '2DL5', 'N']
    success, values = call_procedure(proc_name, proc_params, 2, proc_params2, cursor, log)
    if success:
        log.info("\t=> Success!")
        [part1, part2] = values
        if "2DL5A" in part1:
            A = part1
            B = part2
        else:
            A = part2
            B = part1

        A_alleles = A.replace("2DL5A*", "")
        B_alleles = B.replace("2DL5B*", "")
    else:
        log.info("\t=> Procedure call did not work. :-(")
        A_alleles = ""
        B_alleles = ""

    return A_alleles, B_alleles


def fill_pretypings_dic(mylocus, alleles, pretypings_dic):
    """ add data of one locus to pretypings_dic, separated into 4 columns for 4 possible alleles
    """
    for i in range(4):
        col_name = "{}-{}".format(mylocus, i + 1)  # 4 columns per KIR locus
        if i < len(alleles):
            pretypings_dic[col_name] = alleles[i]
        else:
            pretypings_dic[col_name] = ""


def reformat_pretypings(allele_data, gene, cursor, log, fields = 2):
    """reformat the pretypings data from limsrep into the right format for the pretypings file
    """
    pretypings_dic = {}
    GL_query = f"""with data as
                (select :1 gl_string from dual)
                select gl_strings_mgmt.gl_string@ngsa(gl_string,felder=>{fields})
                from data"""
    cursor.prepare(GL_query)
    items = []
    KIR_loci = []

    target_is_KIR = False  # is the allele to be submitted a KIR allele?
    if gene.startswith("KIR"):
        target_is_KIR = True
    else:
        log.debug("Target allele is not a KIR gene => ignoring KIR pretypings!")
    for row in allele_data:
        (locus, allele1, allele2) = row
        if allele1:
            if locus.startswith("HLA"):
                pretypings_dic[locus + "_1"] = allele1
                pretypings_dic[locus + "_2"] = allele2
            elif locus in ["MICA", "MICB"]:
                pretypings_dic[locus] = allele1
            elif locus == "KIR":
                pass
            else:  # KIR
                if not target_is_KIR:
                    continue
                mylocus = "KIR" + locus
                if locus == "2DS4N":
                    mylocus = "KIR2DS4"
                    typing_2DS4 = items[-1][0]
                    if KIR_loci[-1] == "KIR2DS4":
                        items = items[:-1]
                        allele1 = typing_2DS4 + "+" + allele1
                    else:
                        log.error("KIR2DS4N handling only works correctly if the 2DS4N row is directly preceded by 2DS4. Here, it is preceded by {} insteads. Rejecting!".format(KIR_loci[-1]))
                        raise ValueError("Could not correctly puzzle KIR2DS4 and 2DS4N together. Please contact the TypeLoader staff!")
                        return None

                elif locus == "2DL5":
                    KIR_loci.append(mylocus)

                else:
                    KIR_loci.append(mylocus)
                    
                items.append([allele1, ])
            
    # reformat KIR:
    for i, params in enumerate(items):
        mylocus = KIR_loci[i]
        cursor.execute(None, params)
        mydata = cursor.fetchall()
        try:
            GL = mydata[0][0]
        except Exception:
            GL = ""
        if not GL:  # got None as result
            GL = ""
        # only keep "NEW" in target gene, all others should fall back to POS (or 1field) as per request of IPD
        if "NEW" in GL or "POS" in GL:
            if mylocus != gene:
                GL = "POS"
        if mylocus == "KIR2DL5":
            alleles = [GL]  # keep GL intact and split later by A and B
        else:
            alleles = split_GL_string(GL)
        fill_pretypings_dic(mylocus, alleles, pretypings_dic)

    # postprocessing for 2DL5A/B:
    if "KIR2DL5-1" in pretypings_dic:  # if pretypings contain 2DL5
        GL = pretypings_dic["KIR2DL5-1"]
        GLs = split_2DL5AB(GL, cursor, log)  # list of GL strings separated by A and B
        loci = ["KIR2DL5A", "KIR2DL5B"]

        for i in range(len(GLs)):
            alleles = split_GL_string(GLs[i])
            fill_pretypings_dic(loci[i], alleles, pretypings_dic)

        for col in ["KIR2DL5-1", "KIR2DL5-2", "KIR2DL5-3", "KIR2DL5-4"]:
            pretypings_dic.pop(col, None)

    return pretypings_dic
    

def get_pretypings_from_limsrep(input_params, local_cf, log):
    """retrieves pretypings directly from LIMSREP,
    returns them as dict of dicts:  pretypings[sample_id_int] = {column_name: column_content}
    """
    log.info("Retrieving raw pretypings from external database...")
    ngsrep_scheme = DB_scheme(name = local_cf.get("db", "dbname_ngsrep"),
                       db = local_cf.get("db", "SID_ngsrep"),
                       host = local_cf.get("db", "dbserver_ngsrep"),
                       user = local_cf.get("db", "dbuser_ngsrep"),
                       pwd = local_cf.get("db", "dbpwd_ngsrep")
                       )
    
    ngsm_scheme = DB_scheme(name = local_cf.get("db", "dbname_ngsm"),
                       db = local_cf.get("db", "SID_ngsm"),
                       host = local_cf.get("db", "dbserver_ngsm"),
                       user = local_cf.get("db", "dbuser_ngsm"),
                       pwd = local_cf.get("db", "dbpwd_ngsm")
                       )
    
    samples = [[sample_id] for [sample_id, _] in input_params]
    query_pretypings = "SELECT gene, allele1, allele2 FROM LIMSREP.NEXTYPE_DONOR_BEFU WHERE LIMS_DONOR_ID = :1"
    data_pretypings = query_many(ngsrep_scheme, query_pretypings, samples, log)
    
    query_samples = "select lims_donor_id, spendernr, auftraggeber from limsrep.lims_auftraege where lims_donor_id = :1"
    data_samples = query_many(ngsrep_scheme, query_samples, samples, log)
    
    # reformat data:
    log.info("Reformatting sample infos...")
    sample_dic = {}
    not_found = []
    for i, result in enumerate(data_samples):
        if result:
            [(sample_id_int, sample_id_ext, client)] = result
            sample_dic[sample_id_int] = [sample_id_int, sample_id_ext, client]
        else:
            [sample_id_int] = samples[i]
            not_found.append(sample_id_int)
    
    log.info("Reformatting pretypings...")
    conn, cursor = open_connection(ngsm_scheme, log)
    try:
        pretypings = {}
        for i, allele_data in enumerate(data_pretypings):
            [sample_id_int, gene] = input_params[i]
            if not sample_id_int in not_found:
                log.info("\t{}...".format(sample_id_int))
                pretypings[sample_id_int] = reformat_pretypings(allele_data, gene, cursor, log)
    except Exception:
        close_connection(conn, cursor, log)
        raise
    close_connection(conn, cursor, log)
    log.info("=> reformatting complete!")
    return pretypings, sample_dic, not_found


def write_pretypings_file(pretypings, samples, output_file, log):
    """generate pretypings file
    """
    log.info("Writing pretypings to file {}...".format(output_file))
    columns = ['HLA-A_1', 'HLA-A_2', 'HLA-B_1', 'HLA-B_2', 'HLA-C_1', 'HLA-C_2', 'HLA-DRB1_1', 'HLA-DRB1_2', 
               'HLA-DQB1_1', 'HLA-DQB1_2', 'HLA-DPB1_1', 'HLA-DPB1_2', 'HLA-E_1', 'HLA-E_2', 'MICA', 'MICB', 
               'KIR2DL1-1', 'KIR2DL1-2', 'KIR2DL1-3', 'KIR2DL1-4', 'KIR2DL2-1', 'KIR2DL2-2', 'KIR2DL2-3', 'KIR2DL2-4', 
               'KIR2DL3-1', 'KIR2DL3-2', 'KIR2DL3-3', 'KIR2DL3-4', 'KIR2DL4-1', 'KIR2DL4-2', 'KIR2DL4-3', 'KIR2DL4-4', 
               'KIR2DL5A-1', 'KIR2DL5A-2', 'KIR2DL5A-3', 'KIR2DL5A-4', 'KIR2DL5B-1', 'KIR2DL5B-2', 'KIR2DL5B-3',
               'KIR2DL5B-4', 'KIR2DP1-1', 'KIR2DP1-2', 'KIR2DP1-3', 'KIR2DP1-4',
               'KIR2DS1-1', 'KIR2DS1-2', 'KIR2DS1-3', 'KIR2DS1-4', 'KIR2DS2-1', 'KIR2DS2-2', 'KIR2DS2-3', 'KIR2DS2-4', 
               'KIR2DS3-1', 'KIR2DS3-2', 'KIR2DS3-3', 'KIR2DS3-4', 'KIR2DS4-1', 'KIR2DS4-2', 'KIR2DS4-3', 'KIR2DS4-4', 
               'KIR2DS5-1', 'KIR2DS5-2', 'KIR2DS5-3', 'KIR2DS5-4', 'KIR3DL1-1', 'KIR3DL1-2', 'KIR3DL1-3', 'KIR3DL1-4', 
               'KIR3DL2-1', 'KIR3DL2-2', 'KIR3DL2-3', 'KIR3DL2-4', 'KIR3DL3-1', 'KIR3DL3-2', 'KIR3DL3-3', 'KIR3DL3-4', 
               'KIR3DP1-1', 'KIR3DP1-2', 'KIR3DP1-3', 'KIR3DP1-4', 'KIR3DS1-1', 'KIR3DS1-2', 'KIR3DS1-3', 'KIR3DS1-4']

    with open(output_file, "w", newline = "") as g:
        data = csv.writer(g, delimiter=",")
        header = ['sample_ID_int', 'sample_id_ext', 'client'] + columns
        data.writerow(header)
        
        i = 0
        for sample in pretypings:
            row = samples[sample]
            pretypings_dic = pretypings[sample]
            not_found = []
            for col in columns:
                if col in pretypings_dic:
                    mytyping = pretypings_dic[col]
                else:
                    mytyping = ""
                    not_found.append(col)
                if mytyping:
                    if mytyping.startswith("0"):
                        if mytyping.isdigit():
                            mytyping = "'{}'".format(mytyping)
                row.append(mytyping)
            data.writerow(row)
            i += 1
            if not_found:
                log.debug("\t{}: no pretypings found for {} columns: {}".format(sample, len(not_found), ",".join(not_found)))
    log.info("\t=> written {} rows for {} alleles".format(i, len(samples)))
                
        

pass
#===========================================================
# main:

def read_local_settings(log):
    """reads settings from local config file,
    returns ConfigParser object
    """
    from configparser import ConfigParser
    local_config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config_local.ini")
    log.info("Reading local settings from {}...".format(local_config_file))

    if os.path.exists(local_config_file):
        cf = ConfigParser()
        cf.read(local_config_file)
    else:
        return False
    return cf


def main(log):
    from GUI_login import get_settings

    alleles = [['ID17530942', 'KIR2DL5B']
               ]
    local_cf = read_local_settings(log)
    pretypings, samples, not_found = get_pretypings_from_limsrep(alleles, local_cf, log)

    for sample in pretypings:
        for col in pretypings[sample]:
            if col.startswith("KIR2DL5"):
                print(col, pretypings[sample][col])

    # typing = "00101A/00104A/00601B/00602B/00603B/00801B/00803B/01201A/01202A"
    # split_2DL5AB(typing, log)


    # write_pretypings_file(pretypings, samples, output_file, log)
    
        
if __name__ == '__main__':
    log = general.start_log(level="DEBUG")
    log.info("<Start {} V{}>".format(os.path.basename(__file__), __version__))
    main(log)
    log.info("<End>")


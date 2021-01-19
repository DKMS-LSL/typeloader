#!/usr/bin/env python3
# -*- coding: cp1252 -*-
'''
Created on 20.03.2018

db_internal.py

setup of the internal Typeloader-SQLite db
& functions to fill it with data from .csv files

@author: Bianca Schoene
'''

# import modules:

import sys, os, csv
import sqlite3
import general

from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtSql import QSqlQuery

# ===========================================================
# parameters:

log_file = r"typeloader_db_internal.log"

tables_dir = "tables"

headers = ["Internal Donor-ID", "Allele Nr. in Sample", "Project Name",
           "Allele Nr. in Project",
           "Cell Line", "Internal Name", "Gene", "Goal", "Allele Status",
           "Lab Status",
           "Internal Allele Name", "Official Allele Name"]
headers = ["Software", "Software Version", "Genotyping Date"]

alleles_header_dic = {
    0: "Internal Sample ID",
    1: "Allele Nr. in Sample",
    2: "Project Name",
    3: "Nr. in Project",
    4: "Cell Line (Old)",
    5: "Allele Name",
    6: "Gene",
    7: 'Goal',
    8: "Allele Status",
    9: "Original Allele #1",
    10: "Original Allele #2",
    11: "Software",
    12: "Software Version",
    13: "Genotyping Date",
    14: "Lab Status",
    15: 'Panel',
    16: 'Position',
    17: "Short Read Data?",
    18: 'SR Phased?',
    19: 'SR Technology',
    20: 'Long Read Data?',
    21: 'LR Phased?',
    22: 'LR Technology',
    23: 'Comment',
    24: 'Target Allele',
    25: 'Partner Allele',
    26: 'Mismatch Position',
    27: 'Null Allele?',
    28: "Software (new)",
    29: 'Software Version',
    30: 'Genotyping Date',
    31: 'Reference Database',
    32: 'Database Version',
    33: 'Internal Allele Name',
    34: 'Official Allele Name',
    35: 'New or confirmed?',
    36: "ENA Submission ID",
    37: 'ENA Acception Date',
    38: 'ENA Accession Nr',
    39: "IPD Submission ID",
    40: "IPD Submission Nr",
    41: 'HWS Submission Nr',
    42: 'IPD Acception Date',
    43: 'IPD Release',
    44: 'Upload Date',
    45: 'Detection Date',
    47: "External Sample ID",
    48: "Cell Line",
    49: "Customer",
    50: "Project Name",
    51: "ENA Submission ID",
    52: "Alleles in ENA Submission",
    53: "Timestamp Sent (ENA Submission)",
    54: "Timestamp Confirmed (ENA Submission)",
    55: "Analysis Accession Nr",
    56: "Submission Accession Nr",
    57: "ENA Submission successful?",
    58: "IPD Submission ID",
    59: "Alleles in IPD Submission",
    60: "Timestamp Ready (IPD Submission)",
    61: "Timestamp Confirmed (IPD Submission)",
    62: "IPD Submission successful?"
}


# ===========================================================
# classes:


# ===========================================================
# functions:

def open_connection(db_file, log):
    """opens connection to a .db file
    """
    log.debug("Opening connection to {}...".format(db_file))
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        log.debug("\t=> Connection opened successfully.")
    except Exception as E:
        log.exception(E)
        log.error("\t=> Could not open db connection to {}!".format(db_file))
        conn = None
        cursor = None
    return conn, cursor


def error_in_query(q, task, log):
    """call after every q.exec_ to check for errors;
    logs error and problematic query,
    returns error message for QMessagebox if error found,
     False if no error found
    """
    lasterr = q.lastError()
    if lasterr.isValid():
        msg = "An error occurred while {}:".format(task)
        log.error(msg)
        log.error('FAILED QUERY: "{}"'.format(q.lastQuery()))
        return msg + "\n\n{}".format(lasterr.text())
    else:
        return False


def execute_query(query, num_columns, log, task, err_type="Database Error", parent=None):
    """executes a query;
    returns data of a SELECT statement as list of lists;
    reports errors to log and QMessageBox 
        (using task and err_type as message building blocks)
        
    usage example: 
    success, data = db_internal.execute_query(query, 1, self.log, 
                                              "generating the IPD submission number", 
                                              "IPD submission nr error", self)
    """
    log.debug("\tExecuting query {}[...]...".format(query.split("\n")[0][:100]))
    data = []
    success = False
    q = QSqlQuery()
    q.exec_(query)

    err_msg = error_in_query(q, task, log)
    if err_msg:
        if parent:
            QMessageBox.warning(parent, err_type, err_msg)
        data = err_msg
        return success, data

    success = True
    while q.next():  # if query has return-data, return it
        row = []
        for i in range(num_columns):
            row.append(q.value(i))
        data.append(row)
    q.finish()
    if data:
        log.debug("\t=> {} records found!".format(len(data)))
    return success, data


def check_error(q, mydb, log):
    """call after every q.exec_ to check for errors
    """
    lasterr = q.lastError()
    if lasterr.isValid():
        log.error(lasterr.text())
        mydb.close()
        exit(1)


def execute_transaction(queries, mydb, log, task, err_type="Database Error", parent=None):
    """executes a list of queries in a transaction;
    reports errors to log and QMessageBox 
        (using task and err_type as message building blocks)
    """
    log.debug("\tStarting transaction...")
    success = False

    mydb.transaction()
    q = QSqlQuery()
    i = 0
    for query in queries:
        i += 1
        log.debug("\t\tQuery #{}: '{}[...]...'".format(i, query.split("\n")[0][:50]))
        q.exec_(query)
        err_msg = error_in_query(q, task, log)
        if err_msg:
            if parent:
                QMessageBox.warning(parent, err_type, err_msg)
            mydb.rollback()
            return success

    success = True
    mydb.commit()
    log.debug("\t=> transaction successful")
    return success


def read_table(table_csv, log, make_dummy=False):
    """reads columns of a table from a .csv file 
    and generates lines for a CREATE TABLE statement,
    returns list of these lines;
    if make_dummy, creates an empty dummy .csv with all columns,
        to insert dummy data
    """
    log.debug("Reading columns from {}...".format(table_csv))
    with open(table_csv, "r") as f:
        column_list = []
        columns = []
        values = []
        data = csv.reader(f, delimiter=",")
        for row in data:
            if len(row) > 1:
                if row[0]:
                    if row[0] != "Column":
                        column = row[0].upper()
                        mytype = row[1]
                        try:
                            pk = row[2]
                            if pk:
                                pk = "PRIMARY KEY"
                                log.debug("\tPRIMARY KEY: {}".format(column))
                        except IndexError:
                            pk = ""
                        example = row[-1]
                        column_string = "{} {} {}".format(column, mytype, pk)
                        column_list.append(column_string)
                        columns.append(column)
                        values.append(example)
    log.debug("\t=> {} columns found".format(len(column_list)))

    if make_dummy:  # create an empty dummy .csv with the right columns
        dummy_file = table_csv[:-4] + "_dummy_raw.csv"
        with open(dummy_file, "w") as g:
            g.write(",".join(columns) + "\n")  # header
            g.write(",".join(values) + "\n")  # example row

    return column_list


def create_table(table_name, column_list, cursor, log):
    """creates a table in the SQLite db
    """
    log.debug("Creating table {}...".format(table_name))
    cursor.execute("DROP TABLE IF EXISTS {}".format(table_name))
    create_query = """CREATE TABLE {}
    ({});""".format(table_name, ",\n".join(column_list))
    try:
        cursor.execute(create_query)
    #         print(create_query.replace("TEXT", "VARCHAR2(20)").replace("INT", "NUMBER").replace("TABLE ", "TABLE TL_"))
    except Exception as E:
        log.exception(E)
        log.debug(create_query)
    log.debug("\t=> successfully created")


def fill_table_from_dummy(table_name, cursor, log):
    """fills table with data from its dummy-file
    """
    dummy_file = os.path.join(tables_dir, "{}_dummy.csv".format(table_name.lower()))
    log.debug("Filling table {} with data from {}...".format(table_name, dummy_file))
    try:
        with open(dummy_file, "r") as f:
            data = csv.reader(f, delimiter=",")
            for (i, row) in enumerate(data):
                if i != 0:
                    values = ""
                    for item in row:
                        try:
                            item = int(item)
                            values += "{}, ".format(item)
                        except ValueError:
                            values += "'{}', ".format(item)
                    query = "INSERT INTO {} VALUES ({});".format(table_name, values[:-2])
                    cursor.execute(query)
        log.debug("\t=> {} rows written".format(i))
    except IOError:
        log.warning("Could not find {} => nothing added to table!".format(dummy_file))


def make_tables(cursor, log, tables, insert_dummy_data=False):
    """creates tables for all .csv files in tables_dir
    """
    log.info("Creating tables...")
    for myfile in os.listdir(tables_dir):
        if os.path.basename(myfile.split(".")[0]) in tables:
            mytable = myfile.split(".")[0].upper()
            log.info("\t{}...".format(mytable))
            column_list = read_table(os.path.join(tables_dir, myfile), log, make_dummy=False)
            create_table(mytable, column_list, cursor, log)
            if insert_dummy_data:
                fill_table_from_dummy(mytable, cursor, log)


def show_tables(cursor, log, with_content=False):
    """logs all tables currently in the db
    """
    log.info("Current tables:")
    cursor.execute("select name from sqlite_master where type='table';")
    tables = cursor.fetchall()
    for table in tables:
        query = "SELECT * from {};".format(table[0])
        cursor.execute(query)
        data = cursor.fetchall()
        log.info("\t{}: {} row(s)".format(table[0], len(data)))
        if with_content:
            for row in data:
                log.debug(row)


def clean_tables(cursor, log):
    """cleans all tables currently in the db
    """
    log.info("Cleaning all tables:")
    cursor.execute("select name from sqlite_master where type='table';")
    tables = cursor.fetchall()
    for table in tables:
        table = table[0]
        confirmed = general.confirm("Delete all data from table '{}'?".format(table.upper()))
        if confirmed:
            query = "DELETE from {};".format(table)
            cursor.execute(query)


def query_database(query, db_file, log, cursor=None):
    """returns results of a single query (using sqlite)
    """
    conn = None
    log.debug("Querying database...")
    if not cursor:
        conn, cursor = open_connection(db_file, log)
    try:
        cursor.execute(query)
    except:
        print(query)
        cursor.execute(query)
    data = cursor.fetchall()
    log.debug("=> {} rows found".format(len(data)))
    if conn:
        conn.commit()
        cursor.close()
        conn.close()
    return data


def execute_query_sqlite(query, db_file, log, cursor=None):
    """executes a single query
    """
    conn = None
    log.debug("Executing query...")
    if not cursor:
        conn, cursor = open_connection(db_file, log)
    try:
        cursor.execute(query)
    except:
        print(query)
        cursor.execute(query)
    conn.commit()
    log.debug("\t=> Query executed")
    if conn:
        conn.commit()
        cursor.close()
        conn.close()


def make_clean_db(db_file, log):
    """fills db_file with all necessary tables (empty)
    """
    log.info("Creating empty database for new user under {}...".format(db_file))
    conn, cursor = open_connection(db_file, log)

    tables = ["alleles", "samples", "projects", "files",
              "ena_submissions", "ipd_submissions"]
    make_tables(cursor, log, tables, insert_dummy_data=False)

    conn.commit()
    cursor.close()
    conn.close()
    log.info("\t=> Success!")


def show_table(table, cursor, log):
    """shows columns of one table
    """
    log.info("Looking up description of table {}...".format(table))
    query = "PRAGMA table_info({})".format(table)
    cursor.execute(query)
    rows = cursor.fetchall()
    log.info("=> {} rows found".format(len(rows)))
    for row in rows:
        log.info(row)


def show_table_content(table, cursor, log):
    """shows all rows of one table
    """
    log.info("Looking up content of table {}...".format(table))
    query = "SELECT * from {}".format(table)
    cursor.execute(query)
    rows = cursor.fetchall()
    log.info("=> {} rows found".format(len(rows)))
    for row in rows:
        log.info(row)


pass


# ===========================================================
# main:

def main(log):
    query = "select cell_line, blast_xml, ena_file from files where sample_id_int = :1 and cell_line = :2"
    items = [('ID15220988', 'DKMS-LSL-DPB1-3748'),
             ('ID10865789', 'DKMS-LSL-DPB1-394')]


#     db_file = r"\\nasdd12\daten\data\Typeloader\admin\data.db"
# #     cleanup_missing_cell_lines_in_files_table(log, db_file)
#     conn, cursor = open_connection(db_file, log)
#     query = """select alleles.sample_id_int, alleles.IPD_submission_id, 
#             ipd_submissions.Timestamp_sent, ipd_submissions.Timestamp_confirmed, 
#             ipd_submissions.success,
#             alleles.IPD_submission_nr, alleles.HWS_submission_nr, 
#             alleles.IPD_acception_date, alleles.IPD_release
#         from alleles join ipd_submissions
#             on alleles.IPD_submission_id = ipd_submissions.submission_id
#     where alleles.sample_id_int = 'ID908158'
#         """
# # #     query = "select distinct cell_line from files order by cell_line"
# #     query = "select * from files where cell_line is Null"
# # #     query = "update FILES set cell_line = 'DKMS-LSL-B-4' where sample_id_int = 'ID705918' and allele_nr = 1"
#     data = query_database(query, db_file, log, cursor)
#     print(data)
# #     for (cl,) in data:
# #         print (cl)
# #     
# #     show_table_content("files", cursor, log)
#     cursor.close()
#     conn.close()


if __name__ == '__main__':
    log = general.start_log(level="DEBUG")
    log.info("<Start {}>".format(os.path.basename(__file__)))
    main(log)
    log.info("<End>")

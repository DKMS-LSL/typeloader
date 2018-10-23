"""
update_referce.py

handles updating of the reference data for TypeLoader
"""
import os
import re, subprocess, shutil
import urllib.request
import hashlib
from time import time

from . import hla_embl_parser

remote_db_path = { \
            "hla_path" : "https://github.com/ANHIG/IMGTHLA/raw/Latest/hla.dat", \
            "kir_path" : "https://github.com/ANHIG/IPDKIR/raw/Latest/KIR.dat" \
            }

remote_checksumfile_index = { \
            "kir_checksums_file" : "https://raw.githubusercontent.com/ANHIG/IPDKIR/Latest/md5checksum.txt", \
            "hla_checksums_file" : "https://raw.githubusercontent.com/ANHIG/IMGTHLA/Latest/md5checksum.txt" \
            }


def local_file_from_today(local_ref_file, log):
    """checks last modified date of local file, returns True if it was modified today, else False
    """
    modify_date = os.path.getmtime(local_ref_file)
    now = time()
    diff = now - modify_date
    if diff < 86400: # 60 sec * 60 min * 24 h = file from today
        log.info("\tReference file was already updated today => not updating again")
        return True
    return False
    

def get_remote_md5checksum(db_name, log):
    """retrieves MD5 checksum from IPD's checksum_file 
    """
    log.debug("\tGetting checksum of current remote file...")
    remote_checksumfile = remote_checksumfile_index["%s_checksums_file" % db_name]
    checksum_response = urllib.request.urlopen(remote_checksumfile, timeout=5)
    checksum_data = checksum_response.read().decode("utf-8") 

    # The checksum_data are in lines of the form MD5 (hla.dat) = 2dde3a26abf52c11a70aae7fa8f14666\n
    pattern = ".*%s.dat\) = (.*)\n" % db_name
    datFile_regex = re.compile(pattern)
    match = datFile_regex.search(checksum_data)
    if match:
        md5 = match.groups()[0]
        log.debug("\t=> {}".format(md5))
    else:
        md5 = None
        msg = "Could not find MD5 checksum of remote {} file!".format(db_name)
        log.error(msg)
    return md5


def get_local_md5checksum(local_reference_file, log):
    """gets the MD5 checksum of the current local database version
    """
    log.debug("\tGetting checksum of local file...")
    
    md5 = hashlib.md5(open(local_reference_file, "rb").read()).hexdigest()
    log.debug("\t=> {}".format(md5))
    return md5


def make_blast_db(target, ref_dir, blast_path, log):
    """calls blast to create the local blast database for TypeLoader;
    returns success (=BOOL), msg (=String if error; None if not)
    """
    log.debug("\tCreating local blast database...")
    makeblastdb = os.path.join(blast_path, "makeblastdb")
    cmd = "{} -dbtype nucl -in {}/parsed{}.fa".format(makeblastdb, ref_dir, target)
    try:
        subprocess.run(cmd, check=True)
        return True, None
    
    except Exception as E:
        log.exception(E)
        msg = "Could not create local blast database:\n{}\n".format(repr(E))
        msg += cmd
        log.debug(cmd)
        return False, msg
    

def move_files(ref_path_temp, ref_path, target, log):
    """moves all files from ref_path_temp to ref_path, replacing existing files
    """
    log.debug("\tReplacing old files with new files...")
    for myfile in os.listdir(ref_path_temp):
        if target.lower() in myfile.lower():
            src_path = os.path.join(ref_path_temp, myfile)
            target_path = os.path.join(ref_path, myfile)
            log.debug("\t\t- {}".format(myfile))
            if os.path.exists(target_path):
                os.remove(target_path)
            shutil.move(src_path, target_path)
        

def check_database(db_name, reference_local_path, log, skip_if_updated_today = True):
    """checks IPD Github account for new releases
    """
    log.info("Checking {} for IPD update...".format(db_name.upper()))
    if db_name == "kir": 
        use_dbname = "KIR"  # biological databases and consistency in naming are arch enemies 
    else:
        use_dbname = db_name
    
    local_reference_file = os.path.join(reference_local_path, "{}.dat".format(use_dbname))
    if os.path.isfile(local_reference_file):
        if skip_if_updated_today:
            if local_file_from_today(local_reference_file, log):
                return False, "Reference file was already updated today"
        local_md5 = get_local_md5checksum(local_reference_file, log)
        
        remote_md5 = get_remote_md5checksum(db_name, log)
        if not remote_md5:
            log.info("Aborting attempt to update the {} reference".format(db_name))
            return False, "Could not reach IPD's checksum file"
        
        if remote_md5 == local_md5:
            msg = "\t=> {} is up to date".format(db_name)
            log.info(msg) 
            return False, msg
    
    else:
        log.info("=> No local reference file found")
        local_md5 = None # if reference file does not exist, download it
    
    msg = "=> Found new reference version for {}".format(db_name)
    log.info(msg)
    return True, msg


def update_database(db_name, reference_local_path, blast_path, log):
    """updates a reference database
    """
    log.info("Retrieving new database version for {}...".format(db_name))
    update_msg = None
    if db_name == "kir": 
        use_dbname = "KIR"  # biological databases and consistency in naming are arch enemies 
    else:
        use_dbname = db_name
        
    ref_path_temp = os.path.join(reference_local_path, "temp")
    os.makedirs(ref_path_temp, exist_ok = True)
    
    log.debug("\tdownloading new file...")
    remote_db_file = remote_db_path["%s_path" % db_name]
    local_db_file = os.path.join(ref_path_temp, "%s.dat" % use_dbname)
    with urllib.request.urlopen(remote_db_file, timeout = 10) as db_response, open(local_db_file, "wb") as db_local:
        shutil.copyfileobj(db_response, db_local)
    
    log.debug("\t => successfully downloaded new {} file".format(db_name))
     
    log.debug("\tCreating parsed files...")
    version = hla_embl_parser.make_parsed_files(use_dbname, ref_path_temp, log)
    
    success, msg = make_blast_db(use_dbname, ref_path_temp, blast_path, log)
    
    if success:
        update_msg = """IPD has released a new version of {} ({}). I have updated my {} reference data accordingly.""".format(db_name.upper(), version, db_name.upper())
        move_files(ref_path_temp, reference_local_path, db_name, log)
    else:
        log.error(msg)
        update_msg = """IPD has released a new version of {} ({}), but I could not process it (see below). I'll continue to use the old files for now.
        {}""".format(db_name.upper(), version, msg)
          
    log.info(update_msg)
    return update_msg


def start_log(include_lines = False, error_to_email = False, info_to_file = False,
              debug_to_file = False,
              elaborate = False, level = "DEBUG"):
    """starts a logger and returns it for logging,
    if log file is wanted, info_to_file should be the log file destination (path/filename);
    default logging level is set to DEBUG
    """
    import logging, socket, os
    
    script_name = os.path.basename(__file__)
    log = logging.getLogger(script_name)
    
    # set level:
    level = level.upper()
    if level == "DEBUG":
        log.setLevel(logging.DEBUG)
    elif level == "INFO":
        log.setLevel(logging.INFO)
    elif level == "WARNING":
        log.setLevel(logging.WARNING)
    elif level == "ERROR":
        log.setLevel(logging.ERROR)
    elif level == "CRITICAL":
        log.setLevel(logging.CRITICAL)
    else:
        log.setLevel(logging.DEBUG)
        log.warning("Unknown loglevel '%s'! Using DEBUG instead..." % level)
    
    # define logging format:
    if include_lines:
        formatter = logging.Formatter('%(levelname)s [%(asctime)s] - [ln.%(lineno)d] %(message)s')
    elif elaborate:
        formatter = logging.Formatter("[%(asctime)s] %(levelname)s [%(filename)s:%(lineno)s - %(funcName)s] %(message)s")
    else:
        formatter = logging.Formatter('%(levelname)s [%(asctime)s] - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        
    # establish stream handler (instead of print):
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    log.addHandler(stream_handler)
    
    # establish email handler, if needed: (level ERROR)  
    if error_to_email:    
        myport = 25
        myserver = '192.168.2.23'
        nodename = socket.gethostname()
        email_adresses = ['schoene@dkms-lab.de']
        email_handler = logging.handlers.SMTPHandler(mailhost=(myserver, myport),
                                               fromaddr='%s@%s' % (script_name, nodename),
                                               toaddrs=email_adresses,
                                               subject='Error in %s' % script_name)
        email_handler.setFormatter(formatter)
        email_handler.setLevel(logging.ERROR)
        log.addHandler(email_handler)
    
    # establish file handler, if needed: (level INFO)
    if info_to_file:
        file_handler = logging.FileHandler(info_to_file)
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.INFO)
        log.addHandler(file_handler)
    
    if debug_to_file:
        log.debug_handler = logging.FileHandler(debug_to_file)
        log.debug_handler.setFormatter(formatter)
        log.debug_handler.setLevel(logging.DEBUG)
        log.addHandler(log.debug_handler)
    
    return log

pass
#===========================================================
# main:
def main():
    log = start_log(level="DEBUG")
    log.info("<Start>")
    db_list = ["hla", "kir"]
    blast_path = r"Y:\Projects\typeloader\blast-2.7.1+\bin"
    reference_local_path = r"H:\Mitarbeiterordner\Bianca\Eclipse-Workspaces\Python3\Python3\src\typeloader2\src\reference_data2"
    
    for db_name in db_list:
        new_version, msg = check_database(db_name, reference_local_path, log, skip_if_updated_today = False)
        if new_version:
            update_msg = update_database(db_name, reference_local_path, blast_path, log)
            

    log.info("<End>")


if __name__ == '__main__':
    main()
    

    


    













from os import path
import shutil
import urllib.request
import hashlib

remote_db_path = { \
            "hla_path" : "https://github.com/ANHIG/IMGTHLA/raw/Latest/hla.dat", \
            "kir_path" : "https://github.com/ANHIG/IPDKIR/raw/Latest/KIR.dat" \
            }

remote_checksumfile_index = { \
            "kir_checksums_file" : "https://raw.githubusercontent.com/ANHIG/IPDKIR/Latest/md5checksum.txt", \
            "hla_checksums_file" : "https://raw.githubusercontent.com/ANHIG/IMGTHLA/Latest/md5checksum.txt" \
             }    


def get_remote_md5checksum(db_name):

    remote_checksumfile = remote_checksumfile_index["%s_checksums_file" % db_name]
    checksum_response = urllib.request.urlopen(remote_checksumfile)
    checksum_data = checksum_response.read().decode("utf-8") 

    # The checksum_data are in lines of the form MD5 (hla.dat) = 2dde3a26abf52c11a70aae7fa8f14666\n
    datFile_regex = re.compile("((\(%s\.dat\)) = (.*?)\n)" % db_name)

    return datFile_regex.expand("\\3")


def get_local_md5checksum(db_name):

    if db_name == "kir": 
        use_dbname = "KIR"  # biological databases and consistency in naming are arch enemies 
    else:
        use_dbname = db_name

    
    local_reference_file = path.join(reference_location, "%s.dat" % use_dbname)
    
    return hashlib.md5(open(local_reference_file, "rb").read()).hexdigest()


def update_databases(reference_local_path):

    db_list = ["hla", "kir"]

    if db_name == "kir": 
        use_dbname = "KIR"  # biological databases and consistency in naming are arch enemies 
    else:
        use_dbname = db_name
    
    for db_name in db_list:
        if get_remote_md5checksum(db_name) == get_local_md5checksum(db_name): 
            continue

        
        remote_db_file = remote_db_path["%s_path" % db_name]
        local_db_file = path.join(reference_location, "%s.dat" % use_dbname)
        with urllib.request.urlopen(remote_db_file) as db_response, open(local_db_file, "w") as db_local:
            shutile.copyfileobj(db_response, db_local)

    return 


        

    

    


    













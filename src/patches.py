'''
Created on 27.11.2018

patches.py

implements retroactive changes to the database or config files

@author: Bianca Schoene
'''

import os, sys
from configparser import ConfigParser

from GUI_login import base_config_file, raw_config_file, company_config_file, user_config_file

#===========================================================
# functions:

def get_root_path(log):
    """retrieves root_path from config_base.ini
    """
    log.debug("Getting root path from base config file...")
    cf = ConfigParser()
    cf.read(base_config_file)
    root_path = cf.get("Paths", "root_path")
    log.debug("\t{}".format(root_path))
    return root_path

def get_users(root_path, log):
    """finds existing users
    """
    log.debug("Finding existing users...")
    users = []
    for user in os.listdir(root_path):
        if not user.startswith("_") and os.path.isdir(os.path.join(root_path, user)):
            if os.path.isfile(os.path.join(root_path, user, user_config_file)):
                users.append(user)
    log.debug("\t=> {} users found".format(len(users)))
    return users

def patch_config(root_path, users, log):
    """patches all existing config files if necessary
    """
    log.info("Patching config files if necessary...")
    patch_config_file = "config_patchme.ini"
    if not os.path.isfile(patch_config_file):
        log.warning("No patch-config file found!")
        return
    
    cf_patch = ConfigParser()
    cf_patch.read(patch_config_file) # contains new fields to add
    
    config_file_dic = {"Company": company_config_file # format: {section_name: which basic config file must be updated} # it is assumed that all existing user.ini files must always be updated
                   } # only add sections once they need to be patched
    
    patch_for_users = [] # list of (section, key, value) tuples that need to be set in user config files 
    
    # patch basic config files as needed:
    for section in cf_patch.sections():
        my_cf_file = config_file_dic[section]
        cf_to_patch = ConfigParser()
        cf_to_patch.read(my_cf_file)
        needs_editing = False
        for (key, value) in cf_patch.items(section):
            try:
                myvalue = cf_to_patch.get(section, key)
            except:
                myvalue = None
            if value == myvalue: # if not already set
                log.debug("\t{} already up to date".format(key))
            else:
                log.debug("\tNew value in {}: [{}]: {} = {}".format(my_cf_file, section, key, value))
                cf_to_patch.set(section, key, value)
                patch_for_users.append((section, key, value))
                needs_editing = True
        if needs_editing:
            log.debug("\t=> Updating file {}...".format(my_cf_file))
            with open(my_cf_file, "w") as g:
                cf_to_patch.write(g)
        else:
            log.debug("\t=> No patching necessary")
            
    # patch existing user config files:
    if patch_for_users:
        log.debug("Patching individual user config files...")
        for user in users:
            log.debug("\t{}...".format(user))
            user_config = os.path.join(root_path, user, user_config_file)
            cf = ConfigParser()
            cf.read(user_config)
            for (section, key, value) in patch_for_users:
                cf.set(section, key, value)
            with open(user_config, "w") as g:
                cf.write(g)


def check_patching_necessary_linux(log):
    """checks config files for missing values
    """
    from collections import defaultdict
    log.debug("Checking if any config patches necessary...")
    patchme_dic = {company_config_file : {"Company" : ["ipd_shortname", "ipd_submission_length"]}
                   }
    needs_patching = defaultdict(list)
    for config_file in patchme_dic:
        cf = ConfigParser()
        cf.read(config_file)
        for section in patchme_dic[config_file]:
            for option in patchme_dic[config_file][section]:
                if not cf.has_option(section, option):
                    log.warning("""Config files outdated: option '{}' in section [{}] of {} missing, please specify!
                    """.format(option, section, config_file))
                    needs_patching[config_file].append((section, option))
    if needs_patching:
        msg = "The following settings are missing from your TypeLoader config files:\n\n"
        for config_file in needs_patching:
            msg += "{}:\n".format(config_file)
            for (section, option) in needs_patching[config_file]:
                msg += "- [{}]: {}\n".format(section, option)
        msg += "\nPlease add these values manually, then restart TypeLoader!"
        msg += "\n(For more detailed infos, see the user_manual page 'patches.md'.)"
        return True, msg
    return False, None
            

#===========================================================
# main:

def execute_patches(log):
    """executes all patching
    """
    root_path = get_root_path(log)
    users = get_users(root_path, log)
    patch_config(root_path, users, log)
    

if __name__ == '__main__':
    import general
    log = general.start_log(level="DEBUG")
    log.info("<Start patches.py>")
    check_patching_necessary(log)
    log.info("<End patches.py>")
    
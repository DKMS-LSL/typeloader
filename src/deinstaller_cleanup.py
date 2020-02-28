import os
import general

# ===========================================================
# parameters:

installer = "typeloader_installer_new.nsi"  # name of the current installer.nsi file
install_path = r"C:\Program Files (x86)\TypeLoader"  # path where TypeLoader was installed

# ===========================================================
# functions:


def find_files_leftover_after_deinstaller(my_install_path, log):
    """
    traverses the path where TypeLoader was uninstalled
    to see which files and subdirectories are still left after uninstall;
    returns these as a list of file paths and a list of directory paths
    """
    log.info(f"Searching for leftover files in {my_install_path} after deinstaller has run...")
    myfiles = []
    mydirs = []

    for root, dirs, files in os.walk(my_install_path):
        log.debug(f"\tSearching {root}...")
        mydirs.append(root)
        for file in files:
            myfile = os.path.join(root, file)
            myfiles.append(myfile)

    log.info(f"\t=> found {len(myfiles)} files in {len(mydirs)} subdirectories")
    return myfiles, mydirs


def read_installer(myinstaller, log):
    """
    reads the text of the current installer script and returns it as a string
    """
    log.info(f"Reading current installer from {myinstaller}...")
    with open(myinstaller, "r") as f:
        text = f.read()
    log.info(f"\t=> found {len(text)} characters")
    return text


def make_installer_text(myfiles, mydirs, curr_installer_text, log):
    """
    creates removal code for each file and subdir and checks whether the current installer already removes them;
    prints a list of lines that need to be added to the current installer in order to remove everything
    """
    log.info("Creating text to add to installer...")

    file_text = ""
    for file in myfiles:
        line = f'  Delete "{file.replace(install_path, "$INSTDIR")}"\n'
        if line not in curr_installer_text:
            file_text += line

    if file_text:
        print("Remove files:")
        print(file_text)
        print("Please insert these somewhere before the first 'RMDir' line!")
    else:
        log.info("=> All files contained in installer now! :-)")

    dir_text = ""
    for mydir in mydirs[::-1]:
        if mydir != install_path:
            line = f'  RMDir "{mydir.replace(install_path, "$INSTDIR")}"\n'
            if line not in curr_installer_text:
                dir_text += line

    if dir_text:
        print("\nRemove dirs:")
        print(dir_text)
        print("Please insert these at the appropriate places! (Order matters for directory removal.)")
    else:
        log.info("=> All directories contained in installer now! :-)")


def main(log):
    curr_dir = os.path.dirname(os.path.abspath(__file__))
    files, dirs = find_files_leftover_after_deinstaller(install_path, log)
    if files:
        installer_text = read_installer(os.path.join(curr_dir, installer), log)
        make_installer_text(files, dirs, installer_text, log)
    else:
        log.info("=> Installer seems to have caught everything! :-)")


if __name__ == "__main__":
    logger = general.start_log(level="DEBUG")
    logger.info("<Start>")
    main(logger)
    logger.info("<End>")

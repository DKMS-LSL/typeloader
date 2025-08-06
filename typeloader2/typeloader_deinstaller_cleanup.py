import os
import general

# ===========================================================
# parameters:

installer = "typeloader_installer.nsi"  # name of the current installer.nsi file
install_path = r"C:\Program Files (x86)\TypeLoader"  # path where TypeLoader was installed
missing_deletes_file = "missing_delete_lines.txt"
missing_rmdir_file = "missing_remove_dirs.txt"

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


def read_uninstaller(installer_file, log) -> str:
    """
    Returns the uninstaller section of the current installer.nsi file.
    """
    log.info(f"Reading current uninstaller from {installer_file}...")

    uninstaller_lines = []
    found_uninstaller_section = False

    with open(installer_file, "r") as f:
        for line in f:
            if found_uninstaller_section:  # only collect uninstaller part
                uninstaller_lines.append(line)
            elif line.startswith("; UNINSTALLER SECTION"):
                found_uninstaller_section = True

    if not found_uninstaller_section:
        log.warning("Could not find '; UNINSTALLER SECTION' marker in the file")
        return ""

    text = ''.join(uninstaller_lines)
    log.info(f"\t=> found {len(uninstaller_lines)} lines in the uninstaller section")
    return text


def create_removal_code(leftover_files, leftover_dirs, curr_installer_text, log):
    """
    creates removal code for each file and subdir and checks whether the current installer already removes them;
    prints a list of lines that need to be added to the current installer in order to remove everything
    """
    log.info("Creating text to add to uninstaller section of installer.nsi...")

    file_text = ""
    for file_path in leftover_files:
        line = f'  Delete "{file_path.replace(install_path, "$INSTDIR")}"\n'
        if line not in curr_installer_text:
            file_text += line

    if file_text:
        print("Remove files:")
        print(file_text)
        print("Please insert these somewhere before the first 'RMDir' line!")
        print("(e.g. right after the 'Section Uninstall' heading)")
        with open(missing_deletes_file, "w") as g:
            g.write(file_text)
    else:
        log.info("=> All files contained in installer now! :-)")

    dir_text = ""
    for mydir in leftover_dirs[::-1]:
        if mydir != install_path:
            line = f'  RMDir "{mydir.replace(install_path, "$INSTDIR")}"\n'
            if line not in curr_installer_text:
                dir_text += line

    if dir_text:
        print("\nRemove dirs:")
        print(dir_text)
        print("Please insert these at the appropriate places! (Order matters for directory removal.)")
        with open(missing_rmdir_file, "w") as g:
            g.write(dir_text)
    else:
        log.info("=> All directories contained in installer now! :-)")


def main(log):
    curr_dir = os.path.dirname(os.path.abspath(__file__))
    files, dirs = find_files_leftover_after_deinstaller(install_path, log)
    if files or dirs:
        uninstaller_text = read_uninstaller(os.path.join(curr_dir, installer), log)
        create_removal_code(files, dirs, uninstaller_text, log)
    else:
        log.info("=> Installer seems to have caught everything! :-)")


if __name__ == "__main__":
    logger = general.start_log(level="DEBUG")
    logger.info("<Start>")
    main(logger)
    logger.info("<End>")

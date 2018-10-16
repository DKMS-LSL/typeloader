# Version History

## 2.0.1 (2018-10-12)
- Bugfix: if root\_path/_general could not be created during setup, create it during startup (#39)
- Bugfix: catch non-existing or empty config files during startup & exit gracefully (#36)
- improved user manual (#44)
- Bugfix: added table template .csv files to repo (#40)
- improved installer: (#43)
 - installer can now also be used to update an existing installation (this skips the creation of config files)
 - tidied-up headers etc.
 - now based on Python 3.6.6
 - cleaned uninstaller: delete previously leftover dirs (#41)

## 2.0.0 (2018-09-07) - official release to external!
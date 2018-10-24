# Version History

## 2.1.0 (2018-10-23)
### Bugfixes:
- Codon counting on DPB1 is now correct (#1) 
- added missing files and dirs:
 - Windows installer (#42)
 - table .csv files (#40)
### new features:
- check for new reference data on startup & update if necessary (#4)
- add additional line to IPD files to track the typeLoader version (#45)
### Improved user friendliness:
- Navigation area: doubleclick now opens SampleView or ProjectView (#51)
- enable editing of external sample IDs (#33)
- prohibit spaces in project names (#47)
### Adjustments for external users:
- enable and document running on Linux (#35)
- check whether ENA/IPD settings are filled out & create warning if not (#50)
- if blastn not found, generate helpful error message (#46)

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
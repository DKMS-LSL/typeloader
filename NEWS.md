# Version History

## 2.2.0 (2018-12-19)
### new features
- automatic detection of null alleles (#6)
- policy change with major structural changes: the local_name is now the unique allele identifier, whereas cell_line is used for samples (#64)
- IPD filenames, cell lines and local_names are now generated automatically (#57, #64)
- added allele history tab to AlleleView (#10)
- added dialog to view user manual (#70)
- download an example pretypings file (#55)
- checks and popups to guide new users (#54) 
 
### Bugfixes:
- sequences with incomplete UTR3 are now rejected (previously, they were accepted but produced buggy outcome) (#62)
- workaround for ENA bug (certain sequences were unfairly rejected) (#53)
	
### Updated user manual
- new: future features
- new: elaborate first_start page to get new users started
- adjusted to all changes 

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
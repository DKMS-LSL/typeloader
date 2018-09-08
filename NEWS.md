# Version History

## 2.0.0 (2018-09-07) - official release to external!
### New Features:
- User and password handling:
 - passwords now enabled (#85)
 - add new users through the GUI (#84)
 - new UserSettings dialog, where users can change their settings (inkl. changing their passwords) (#14)
 - use individual user's data to generate IPD files (#96)
- added "Download Files" und "Edit a File" buttons & funtionality to ProjectView
- added user manual (#131)
- created installer (#69)
- checks for new version during login (#151)  
### Improvements:
### Functional:
- FileEditDialogs can now handle XML files (#89)
- better protection against accidental mistakes 
 - cell-lines can only contain alphanumeric characters or - or _ (#96) 
 - ProjectView is now non-editable + has a button to change project status (#100)
 - in all editable tables, editing has been restricted to such cells where editing makes sense (#122)
 - cells that expect certain values now have Comboboxes for edits (#50)
- IPDSubmissionForm now accepts , or ; as delimiter for pretyping file (#144)
- timestamp of uploading of novel alleles is now recorded (#140)
- added shortcuts to all menu options (#44)
- BugFix: if IPD submission was successfully created, use "yes" instead of "True" (#138)
- BugFix: IMGT-files with appendix _confirmation are now handled correctly (#147)
### Optical:
- new icon and splashscreen (#34, #141)
- decent headers for almost all tables (single exception: last row of IPD Tab in AlleleView) (#48)
- automatic refreshing of all Overviews after individual changes should work now (#160)

### Back End:
- major code cleanup & restructuring
 - execute all db interactions through PyQSql (once that connection is opened) 
 - moved different views into separate submodules (#127)
 - improved logging (various)
- added unit tests for data displayed in all views (#129)
- moved desttings to config.ini files, which are created during setup & user creation (#143)
- prepared for running on external machines

## 0.1.3 (2018-07-19)
- new feature: bulk fasta upload (#101, closed)
- code cleanup: move functions from GUI into typeloader_functions.py (#123, ongoing)
- added Readme.md for test suite

## 0.1.2 (2018-07-16)
- new core feature: IPD files can now be created for confirmatory/known alleles, as well (backported to web GUI version)
- cell_lines are now shown in the allele lists of ProjectView and SampleView (#107)
- ENA rejection message now shows name and cell-line of rejected sample, not just number within submission (#108)
- SampleView allele list now shows all alleles of a sample, even across projects (#113)
- BugFix: restrict adding of new alleles and submission to IPD and ENA to open projects (#112)
- BugFix: allele nr of allele within sample is now calculated cross-project (#113)
- BugFix: navigation no longer collapses all other projects just because a project was selected (follow-up to #105)
- status values have been adjusted to make more sense (#110)
- new option to delete an allele cleanly (needs a password => only for admins) (#111)
- get customer from pretyping file during IPD submission and store it in table SAMPLES (#114)
- Bugfixes on IPDSubmissionForm:
	- closing IPD submission should not collapse navigation (leftover from #105)
 	- pass current project as preselection to IPDSubmissionForm (#116)
 	- IPDSubmissionForm now accessible from ProjectsOverview (#117)

## 0.1.1 (2018-07-12)
- improved handling of rejections during ENA submission (#102, #104)
- Bugfix: improved navigation (does not collapse after changes anymore) (#105)

## 0.1.0 (2018-07-10)
- first release (beta test)

## 0.0.0 (2018-03-13)
- project started

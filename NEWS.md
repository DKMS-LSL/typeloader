# Version History

## V2.5.1 (2019-10-21)
- During IPD file creation, reject GL strings in non-KIR loci (#123)

## V2.5.0 (2019-09-11)
### Bugfixes:
- in IPD files, now the correct pretyping delimiter (comma or plus) is used even if both alleles are novel (#122) 
- correctly catch and display errors from ENA submission, if they happen

## V2.4.1 (2019-08-07)
### Changes:
- the Windows installer is now provided via GitHub release and is no longer part of the repository itself (#120)

## V2.4.0 (2019-07-15)
### New features:
- ENA submission is now handled through the new Webin-CLI (#100)
- added support for DPA1 and DQA1 (#118)

### Changes & adjustments:
- pretypings are now limited to HLA, KIR and MIC, as per IPD request (#119)
- if allele belongs to an unsupported locus, raise a meaningful error (#118)
- New Projects: all fields are now checked for disallowed characters (#116)

### Behind the scenes:
- moved ENA submission functionality from ENASubmissionForm to typeloader_functions (#14) 

## V2.3.2.1 (2019-06-18)
### Bugfix:
- target alleles with a deletion and a mismatch near the end of the CDS can now be handled (#113)

## V2.3.2 (2019-05-29)
### New features:
- users can delete individual alleles or all alleles of a project by rightclicking in the navigation area (on an allele or project, respectively)
- DKMS-users can now retrieve pretypings directly from the database (#16, #84)
- BothAllelesNovelDialog is now scrollable (#112)

### Changes
- IPD files: fields "name" and "lab\_contact" now contain the general company identifier, while the individual submitter is given as "alt\_contact" (#108)
- all pretypings in IPD files are now consistently formatted as GL-strings
- confirmation IPD files now contain the closest known allele in the description section (#106)

### Bugfixes
- TypeLoader errors during reference updates are now caught (previously led to crashes) (#109)

## V2.3.1.1 (2019-05-07)
### Bugfixes
- various bugfixes to make the Windows installer work

## V2.3.1 (2019-05-03)
### new features
- Format of pretypings file changed (#95)
- IPD reference data: TypeLoader now uses only tested-and-ok versions of IPD's releases, to avoid automatically using broken releases (#99)
- added example files for all gene systems and steps (#88)
- sanity-check for fasta file format (#75)

### Bugfixes:
- the key "sample_id_int" in fasta headers is now recognized correctly (#97)
- handle fasta file extensions beside .fa (#87)
- replaced .locked with _locked to hopefully work for external Windows users (#101)

## 2.3.0 (2019-04-18)
### new features:
- Support for MICA and MICB (#52)
- Support for incomplete sequences: if only the UTRs are partial, TypeLoader now throws a warning but the user can decide to upload anyway. Partially known exons or introns are still rejected (and will continue to be). (#63)

### Bugfixes:
- use class II enumeration for all HLA class II genes, not just DPB1
- many small ones

## 2.2.1 (2019-03-11)
### new features:
- Recognize multiple novel alleles in target locus: this is now checked during IPD file creation amd the files are formatted accordingly. If necessary, user input is requested to clarify which of the given alleles is the target allele. (#72)
- Pretyping checks: TypeLoader now checks whether the data given in the pretypings file fits the target alleles, and requests user changes where necessary to ensure consistent, sensible output. (#82)
- Faster startup: the AlleleOverview, which is used rarely but time-intensive to build, is now only generated on demand. (#80)
- Options for Workflow settings are now consistent with options available through IPD's web form (#78)

### Updated user manual:
- Description for pretypings file is much more elaborate now.

## 2.2.0 (2018-12-19)
### new features:
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
	
### Updated user manual:
- new: future features
- new: elaborate first_start page to get new users started
- new: elaborate instructions how to feed TypeLoader-generated data into IPD's web form
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
# typeloader test suite

Before every push, it's strictly necessary to run the test suite! Further progressing is only permitted, if all tests are successfull!

To run the test, check the windows / linux paths in the settings dictionary. In order to keep the test suite runable on both environments, a [staging] account was created at nasdd11 server in the bioinf/typeloader directory. Within the staging directory, you'll find a [data_unittest] directory, where all the comparison data is stored.  Do not change anything in there!

If you run the test suite, every directory, file, and database entry that was written will be automatically deleted after finishing the tests. With the [staging] account, you use the ENA test server and their FTP server. Files on the ftp server will be deleted automatically after transmission.

## Which tests are in there?

- Test_Create_Project => [tests new project form]
 	- is project_name like [date_user_gene_pool]
 	- check if project dir exists [staging/project_name]
 	- check if project file [staging/project_name/project_name.xml] exists
 	- check if project file [staging/project_name/project_name_sub.xml] exists
 	- check if project file [staging/project_name/project_name_output.xml] exists
 	- check if [alias], [center_name], [project-title] and [project_description] was set in [staging/project_name/project_name.xml]
 	- check if [alias], [center_name], [schema] and [source] was set in [staging/project_name/project_name_sub.xml]
 	- check if [submissionFile], [success], [accession], [alias] and [respond_text] was set in [staging/project_name/project_name_output.xml]
 
- Test_Create_New_Allele => [tests new allele form]
    -  Test both fasta and xml upload
        - check base_name [DKMS-LSL-xx-xx]
        - check traget_allele [KIR3dp1:xxx:new]
        - compare lines of *.ena.txt output
        - check if sample dir exists [staging/project_name/IDxxxxxx]
        - check if sample file [staging/project_name/IDxxxxxx/base_name.blast.xml] exists
        - check if sample file [staging/project_name/IDxxxxxx/base_name.ena.txt] exists
        - check if sample file [staging/project_name/IDxxxxxx/base_name.fa] exists
        - check if sample file [staging/project_name/IDxxxxxx/base_name.xml] exists --> only at gendx xml upload
        - check allele table in sqlite db
        - check files table in sqlite db
        - check samples table in sqlite db
 	    
- Test_Send_To_ENA => [tests submission to ENA form]
    - check if GUI table after project choice and OK clicking has the correct entries 
    - check if [alias], [center_name], [project-title], [project_description], [checksum], [checksum_method], [filename] and [filetype] was set in [staging/project_name/PRJEBxxxx_analysis.xml]
    - check if [alias], [center_name], [schema] and [source] was set in [staging/project_name/PRJEBxxxx_submission.xml]
    - check if [submissionFile], [success], [analysis_accession], [alias_sub_id], [submission_accession], [alias] and [respond_text] was set in [staging/project_name/PRJEBxxxx_output.xml]
    - check ena_submission table in sqlite db

- Test_Send_To_IMGT => [tests submission to IPD form]
    - check if table after project choice and uploading befund and ena respond file has the correct entries 
    - check allele table is updated in sqlite db
    - check ipd_submissions table in sqlite db
    - check if submission file [staging/project_name/IPD-submissions/submission_ID/befund.csv] exists
    - check if submission file [staging/project_name/IPD-submissions/submission_ID/DKMS1000xxxx.txt] exists
    - check if submission file [staging/project_name/IPD-submissions/submission_ID/ena_respond] exists
    - check if submission file [staging/project_name/IPD-submissions/submission_ID/ipd_sub_xxx.zip] exists
    - compare lines of DKMS1000xxxx.txt output

- Test_Make_IMGT_Files0> [tests Make_IMGT_Files in typeloader_core]
    - test if "CC   Confirmation" tag is set if it's an exact match and allele is already in db
    - check if output has an *_confirmation.txt extension

- Test_EMBL_functions
    - check if generate_project_xml generates the correct output
    - check if generate_submission_project_xml generates the correct output
    - check if generate_analysis_xml generates the correct output
    - check if generate_submission_ff_xml generates the correct output
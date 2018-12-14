# ![Icon](images/TypeLoader_32.png) Test Users

If you want a user account to test things, create a user named "test" (or anything starting with "test" (not case sensitive)). 

(This means if your actual name happens to start with "Test", better choose a username that doesn't. ;-)) 

With a test account, you can test the following things without fear of causing problems:

 * Whether your connection to ENA works (usually a matter of proxy settings)
 * Whether your raw files work with TypeLoader
 * Which TypeLoader functions behave in what way

Test user accounts can do everything the other user accounts can do, but they are connected to the ENA test server, not the productive ENA server. So when you create projects or submit alleles to ENA, these are not submitted to the productive server (where getting wrong data deleted requires effort) but to the ENA test server where everything is deleted automatically after 24 hours.

This means that in a test account, you can not submit alleles of projects that were created over 24 hours ago, as these projects will have been deleted from the ENA server.

![Important](images/icon_important.png) **So if you want to test [=> allele submission to ENA](submission_ena.md), best create a fresh project.**

(Since [=> submission to IPD](submission_ipd.md) happens semi-automatically (TypeLoader creates all files, but you have to submit them by email or upload), test users are not necessary to test this process as the files can always be recreated and overwritten.) 
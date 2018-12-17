# ![Icon](images/TypeLoader_32.png) How to use TypeLoader: Getting started
When you start TypeLoader for the first time after [=> Setup](setup.py), you will have to create a [=> User Account](users.md). 

**We *strongly* recommend creating a [=> Test Account](users_test.md) first and using it to get familiar with all of TypeLoader's functions!**

(Unlike other user accounts, test accounts are connected to ENA's test server insted of their productive server. You don't want to screw around on their productive server! ;-))

Once you have created an account and logged into it, TypeLoader will ask whether you want to update the reference data. Since the installation does not bring any reference data along, **you must accept the reference update** for TypeLoader to work!
Just click "Yes" and wait until another Popup appears to tell you that TypeLoader has (hopefully) successfully update its reference data (or give you an error message if a problem was encountered).

After the reference data has been downloaded and processed successfully, you can get familiar with TypeLoader.

If you have not registered with ENA, yet, you should do this now (follow the instructions on [ENA's 'Register Submission Account' page](https://ena-docs.readthedocs.io/en/latest/reg_01.html) and [=> configure your settings accordingly](settings.md) (tab "Company & Communications Settings"). Otherwise, TypeLoader will not be able to work.

Once you have entered communication data with ENA, you can start using TypeLoader by [=> creating a new project](new_project.md). All alleles in TypeLoader must be part of a project (since that is how ENA handles sequences), so you always need a project before you can upload any sequences.

After you have created a project, you can [=> add new alleles](new_allele.md) to it. (Once you are familiar with this method, you can also use the [=> bulk fasta upload](new_allele_bulk.md) to save even more time.)

When your test project contains a handful of alleles, you can submit them to ENA using the [=> ENA submission dialog](submission_ena.md). If there are no problems encountered, all your submitted alleles will now have the status ``ENA submitted``. If ENA has problems with any of your sequences, TypeLoader will show you a popup window explaining the problem, so you can fix them before trying again. 

Once you are satisfied that ENA's test server accepts your sequences, create a productive [=> User Account](users.md) and log into that (and, if necessary, [=> configure its settings, too](settings.md). Create a project and add your sequences, just like you did in the test account.

When your project contains the alleles you want, submit them to ENA. (You do not have to submit all alleles of a project at once, and you can add more alleles to a project after you have submitted other alleles of the same project. To get started, it might be good idea to try out a handful of alleles, submit them, and await the ENA accession numbers, before uploading hundreds of alleles and only then realising a problem with the input format or methodology.)

Once ENA has assigned accession numbers to your alleles, they will send you an email. After you have received that email, you can [=> create IPD submission files](submission_ipd.md). (This, you can do in your productive user account, as there is no direct server interaction with IPD.) For this, you will need to have a .csv file with the genotyping results of all other loci of your samples (you can download an example file from TypeLoader), and the attachment of the ENA email. **You also must make sure to [=> configure the Methods part of your settings](settings.md) to correctly depict your workflow!** 

If you have not ever submitted novel alleles to IPD, open your first submission text file, go to [IPD's submission page](https://www.ebi.ac.uk/ipd/imgt/hla/subs/submit.html) and type the required information into their web form. You need to do this in order to get a submittor ID, which you can then [=> add to your TypeLoader settings](settings.md). 

Once you have a submittor ID, [=> contact IPD to let them know you want to submit TypeLoader files](ipd.md). They will probably ask you to type in a few more alleles by hand, so they can get a feeling for the kind of data you will be submitting, before giving you a way to upload future files directly.

Once IPD has accepted and assigned names to your alleles, they will notify you by email. 

![important](images/icon_important.png) **If you encounter any problems along the way, please do not hesitate to contact us, ideally by  [=> creating a GitHub issue](https://github.com/DKMS-LSL/typeloader/issues)!**
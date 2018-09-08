# ![Icon](images/TypeLoader_32.png) Installing TypeLoader #

## Windows ##
Download the file `Setup_TypeLoader.exe` under `installer` => `windows` and install it with admin privileges. The wizard will guide you through the installation process.

### Important:

During installation, you will be asked to provide certain settings:

1. A path to where the data created with ``TypeLoader`` should be stored 
2. ENA communication settings
3. IPD communication settings

Part 1 is mandatory. Without this, ``TypeLoader`` won't know where to create user accounts and store your data. *This path should NOT be changed later*, so choose a path wisely. (E.g., best not place this on your Desktop, but rather on a partition or drive with plenty of disk space available.) 

All settings in parts 2 and 3 are optional, as they can later be reset from the Settings Dialog. However, if you do not fill these out during setup, you will have to later reset them manually *for each user*. (There is currently no way to reset these settings globally after setup.)

#### ENA Settings:

To submit your alleles to IPD, you first have to submit them to ENA (or GenBank or DDBJ, but TypeLoader uses ENA). To get these data, you have to register with ENA as a sequence submitter (follow the instructions on [ENA's 'Register Submission Account' page](https://ena-docs.readthedocs.io/en/latest/reg_01.html).

 * **Centre Name:** This is the name by which ENA knows your lab.
 * **FTP user:** This is the email address the main ENA contact at your lab.
 * **Password:** This is the corresponding password.
 * **Proxy:** You may need this to get past your firewall. If you know or think you have no proxy, leave this field empty. If in doubt, ask your friendly IT people. 

#### IPD Settings:
You will have to submit your first IPD file by hand (you can let TypeLoader create it, but you will have to manually edit it before sending it out. Then submit it using [IPD's Submission Page](https://www.ebi.ac.uk/ipd/imgt/hla/subs/submit.html). Only then you will receive a submitter ID, which you can use to generate your future submission files with TypeLoader.

**If you have never submitted alleles to IPD, yet, leave these fields empty!**

 * **Lab Name:** This is the name by which IPD knows your lab (given to them as "institute")
 * IPD contact's **Full Name:** This is the name you are registered under.
 * IPD contact's **Form of Address:** This is what you provided as "title". (Dr./Mr./Mrs./Ms. etc)
 * IPD contact's **Email:** This is the email adress you registered with.
 * IPD contact's **Submittor ID:** This is the submitter ID you received from IPD.

## Linux ##
There currently is no Linux installer (though there will be). You should be able to download the code and run it by executing the file ``typeloader_GUI.pyw``, though. (You might have to change its extension to ``typeloader_GUI.py``.) (Needs Python 3.6 or higher, with PyQt5 installed.) 
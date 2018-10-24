# ![Icon](images/TypeLoader_32.png) Installing TypeLoader under Linux

There currently is no Linux installer (though we plan to create one eventually). 

![important](images/icon_important.png) **Please note that TypeLoader is a GUI application, not a command line application. There is no command line version at this point (though there may be one at some point in the future).**

## Dependencies
TypeLoader requires the following dependencies (all versions are minimum versions):

 * Python 3.6.1
 * PyQt5 5.9.2
 * pycurl 7.43.0.1
 * BioPython 1.72
 * xmltodict 0.11.0
 * blastn

### Installing the Python modules:
Once Python3.6 is installed, use pip to install the non-standard modules.

![important](images/icon_important.png) **Do not update pip3 if you can avoid it, it seems to break.**

```
pip3 install PyQt5
pip3 install pycurl
pip3 install BioPython
pip3 install xmltodict

```

### Installing Blastn
Install on debian/Ubuntu with: 

```
sudo apt-get install ncbi-blast+
```

On redhat/fedora, use: 

```
dnf install ncbi-blast+
```

## TypeLoader Setup
Clone the repository to a suitable place on your machine.

### Creating the config files
Typeloader needs two config files (under Windows, these are created through the installer). Under Linux, you must create them manually and save them in the ``src`` folder`of your TypeLoader repository:

#### config_base.ini
This file contains the links to blastn and TypeLoader's data folder.

```
[Paths]
root_path: <path where TypeLoader should store its data>
blast_path: <path to blastn>

```

![important](images/icon_important.png) **Please note that you will have to manually create the directory given as root_path. (The Windows installer does this by itself.)**

![important](images/icon_important.png) **All paths must be absolute paths (starting from /home/), not shortened path (starting with ~).**

#### config_company.ini
This file contains your company-internal settings for communication with ENA and IPD.

**All settings in this file are optional and can be left empty**, as they can later be reset from the Settings Dialog. However, if you do not fill these out during setup, you will have to later reset them manually *for each user* (you can do this from the GUI, using the [=> Settings Dialog](settings.md). (You can reset them globally by editing this file, but this will not affect any already-created users.)

```
[Company]
ftp_user: 
ftp_pwd: 
proxy: 
xml_center_name: 
lab_of_origin: 
lab_contact: 
lab_contact_address: 
lab_contact_email: 
submittor_id:

```

##### ENA Settings:

To submit your alleles to IPD, you first have to submit them to ENA (or GenBank or DDBJ, but TypeLoader uses ENA). To get these data, you have to register with ENA as a sequence submitter (follow the instructions on [ENA's 'Register Submission Account' page](https://ena-docs.readthedocs.io/en/latest/reg_01.html)).


 * **ftp_user:** This is the email address of the main ENA contact at your lab.
 * **ftp_pwd:** This is the corresponding password.
 * **proxy:** You may need this to get past your firewall. If you know or think you have no proxy, leave this field empty. If in doubt, ask your friendly IT people.
 * **xml\_center_name:** This is the name by which ENA knows your lab.

#### IPD Settings:
You will have to submit your first IPD file by hand (you can let TypeLoader create it, but you will have to manually edit it before sending it out). Then submit it using [IPD's Submission Page](https://www.ebi.ac.uk/ipd/imgt/hla/subs/submit.html). Only then will you receive a submitter ID, which you can use to generate your future submission files with TypeLoader.

**If you have never submitted alleles to IPD, yet, leave these fields empty!**

 * **lab\_of_origin:** This is the name by which IPD knows your lab (given to them as "institute")
 * **lab_contact:** This is the name your IPD contact person is registered under.
 * **lab\_contact_address:** Your lab contact's form of address (this is what you provided as "title". (Dr./Mr./Mrs./Ms. etc))
 * **lab\_contact_email:** This is the email adress you registered your IPD contact person with.
 * **submittor_id:** This is the submitter ID you received from IPD.

## Running TypeLoader
Once you have everything set up, rename the file ``src/typeloader_GUI.pyw`` to the extension .py. Then you should be able to execute this as a Python file to run TypeLoader.

See [=> First Start](first_start.md) for how to continue after setup.
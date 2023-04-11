# ![Icon](images/TypeLoader_32.png) Installing TypeLoader under Linux

There currently is no Linux installer. 

![important](images/icon_important.png) **Please note that TypeLoader is a GUI application, not a command line application. There is no command line version at this point (though there may be one at some point in the future).**

## Dependencies
TypeLoader requires the following dependencies (all versions are minimum versions):

 * `Python` 3.10.4 
 * `poetry` 1.3.2
 * `blastn`


### Installing poetry
Once `Python` is installed, you need to install the package manager `poetry`.
 
To install it, please follow the instructions given in [the poetry documentation](https://python-poetry.org/docs/#installation).


### Installing blastn
Install on debian/Ubuntu with: 

```
sudo apt-get install ncbi-blast+
```

On redhat/fedora, use: 

```
dnf install ncbi-blast+
```

## TypeLoader Setup
Clone the repository from [GitHub](https://github.com/DKMS-LSL/typeloader) to a suitable place on your machine.

### Installing Python dependencies via poetry
To install the necessary `Python`dependencies, `cd` into the repository, then call

```
poetry install
```

### Creating the config files
Typeloader needs two config files (under Windows, these are created through the installer). Under Linux, you must create them manually and save them in the `typeloader2` folder of your TypeLoader repository:

#### config_base.ini
This file contains the links to blastn and TypeLoader's data folder.

```
[Paths]
root_path: <path where TypeLoader should store its data>
blast_path: <path to blastn, probably something like /usr/bin/blastn>

```

![important](images/icon_important.png) **All paths must be absolute paths (starting from /home/), not shortened paths (starting with ~).**

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
ipd_shortname:
ipd_submission_lenght: 7
cell_line_token:
last_tl_version: 2.14.0
```

##### ENA Settings

To submit your alleles to IPD, you first have to submit them to ENA (or GenBank or DDBJ, but TypeLoader uses ENA). To get these data, you have to register with ENA as a sequence submitter (follow the instructions on [ENA's 'Register Submission Account' page](https://www.ebi.ac.uk/ena/submit/webin/accountInfo)).


 * **ftp_user:** This is the email address of the main ENA contact at your lab.
 * **ftp_pwd:** This is the corresponding password.
 * **proxy:** You may need this to get past your firewall. If you know or think you have no proxy, leave this field empty. If in doubt, ask your friendly IT people.
 * **xml\_center_name:** This is the name by which ENA knows your lab.

#### IPD Settings
You will have to [register with IPD](https://www.ebi.ac.uk/ipd/submission/register/) in order to get a submittor ID from them.

**If you have never submitted alleles to IPD, yet, leave these fields empty!**

 * **lab\_of_origin:** This is the name by which IPD knows your lab (given to them as "institute")
 * **lab_contact:** This is the name your IPD contact person is registered under.
 * **lab\_contact_address:** Your lab contact's form of address (this is what you provided as "title". (Dr./Mr./Mrs./Ms. etc))
 * **lab\_contact_email:** This is the email adress you registered your IPD contact person with.
 * **submittor_id:** This is the submitter ID you received from IPD.
 * **ipd_shortname:** A short identifier for your lab (ideally an acronym etc). The generated IPD submission file names will start with this. Use only letters or hyphens.
 * **ipd\_submission\_length:** The number of digits used for the allele number in the file names of IPD submission files. We recommend setting this value to 7 as specified in the example above.

#### Other Settings

The following additional settings are also needed:

 * **cell\_line\_token:** A short identifier for your lab (ideally an acronym etc). The generated cell line and allele IDs will start with this. Use only letters or hyphens. (Can be identical to `ipd_shortname`, but doesn't have to.)
 * **last\_tl_version:** This should be the TypeLoader version you are currently installing. It is used internally to handle patches, if they should become necessary.

## Running TypeLoader
Once you have everything set up, rename the file ``typeloader2/typeloader_GUI.pyw`` with the file extension `.py`. Then you should be able to execute this as a `Python` file to run TypeLoader with the following command:

```
poetry run python typeloader2/typeloader_GUI.py
```



See [=> First Start](first_start.md) for how to continue after setup.

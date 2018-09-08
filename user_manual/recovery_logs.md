# ![Icon](images/TypeLoader_32.png) Recovery and Logs

## Database recovery

All metadata within TypeLoader is stored in each account's SQLite database file. Should this file become corrupt or broken at any point, the state of before this session can always be restored. (This should not be necessary, but this is a safety precaution.)

To do this, use your file manager of choice and go to the path where TypeLoader stores its data (specified during install), then choose the folder with your username. In there, there is a folder called recovery, which contains database dumps and log files of the last X days. (X can be specified under ``Settings`` => ``Preferences`` => ``Days to store recovery data``.) 

**Choose the latest version of <timestamp\>_data.db, copy it to the folder above, delete the file data.db there and rename the dump to data.db.**

Each time TypeLoader starts, it creates a dump of the latest version of your database (which should be intact) and saves it there, with a timestamp of when your session started. Each time TypeLoader is closed, it deletes all files in your recovery that have a timestamp older than X days. 

![warning](images/icon_important.png) **This will restore TypeLoader to the state before the current session started! All your changes since then will be lost. If you have made submissions to ENA in the meantime, this will bring you out of synch with them.** 

**So it's a good idea to NOT KEEP TypeLoader RUNNING indefinitely, but close it at least every night.**

## Logs

TypeLoader writes two identical log files for every session:

 * one in the user's recovery dir (<data\_path\>/<username\>/recovery/<timestamp\>.log)
 * one under \<data\_path\>/_general/<timestamp\>.log 

The first logfile gets cleaned up during the same time as old database dumps.

The second logfile is deleted immediately when TypeLoader is closed without crashing. This file is used to give information if TypeLoader crashes before reaching the login screen (at which point it will start writing the first logfile). 
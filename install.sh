#!/bin/bash

bootstrapLink="https://github.com/twbs/bootstrap/releases/download/v3.3.6/bootstrap-3.3.6-dist.zip"
apacheConfLocation="/etc/apache2/apache2.conf"

echo ""
echo ""

echo "--------------------------------------------------------------------------------"
echo "TypeLoader Installer"
echo ""
echo "TypeLoader is developed at the Deutsche Knochenmarkspenderdatei (DKMS) Life"
echo "Science Lab, Dresden, Germany"
echo ""
echo "TypeLoader is released under the GNU Lesser General Public License"
echo "http://www.gnu.org/licenses/lgpl-3.0.txt"
echo ""
echo "For any help or questions, please write Vineeth at surendra@mpi-cbg.de"
echo "--------------------------------------------------------------------------------"

echo ""
echo ""

if [[ $EUID -ne 0 ]]; then
   echo "**Error** This installation must be run as root" 1>&2
   echo "Exiting"
   echo ""
   exit
fi


echo "TypeLoader will now check for Apache, Python and BioPython installations"
echo ""

echo "Checking for Apache2..."
if command -v apache2 > /dev/null
then
    echo "installed"
    echo ""
else
    echo "not installed."
    echo "**Error** Please install Apache2 from http://apache.org/dyn/closer.cgi"
    echo "Exiting"
    echo ""
    exit 
fi

echo "Checking for python..."
if command -v python > /dev/null
then
    echo "installed"
    echo ""
else
    echo "not installed."
    echo "**Error** Please install Python from https://www.python.org/downloads/"
    echo "Exiting"
    echo ""
    exit
fi

echo "Checking for BioPython..."
if python -c "import Bio" > /dev/null 2>&1
then
    echo "installed"
    echo ""
else
    echo "not installed."
    echo "**Error** Please install BioPython from http://biopython.org/wiki/Download"
    echo "Exiting"
    echo ""
    exit
fi

echo "Downloading the Twitter Bootstrap framework..."
rm -rf boostrap* 
if wget $bootstrapLink > /dev/null 2>&1
then
    echo "success."
    echo ""
else
    echo "failed."
    echo "**Error** Please check if wget is installed, also check the status of the Bootstrap link at the beginning of the install script"
    echo "Exiting"
    echo ""
    exit
fi

echo "Extracting downloaded Bootstrap framework..."
unzip bootstrap*.zip > /dev/null 2>&1
rm -f bootstrap*.zip
mv bootstrap* bootstrap
echo "completed."
echo ""

echo "Configuring Apache for TypeLoader ..."
if [ `cat /etc/apache2/apache2.conf | grep -i typeloader | wc -l` -gt 0 ]
then
    echo "skipping. Apache seems to already be configured for TypeLoader."
    echo ""
else
    if cat apacheConfLines.txt >> $apacheConfLocation
    then
        echo "done."
        echo ""
    else
        echo "failed."
        echo "**Error** Please check if the configuration file /etc/apache2/apache2.conf exists"
        echo "Exiting"
        echo ""
        exit
    fi
fi

echo "Configuring folders and copying source files for installation ..."
mkdir -p /export/typeloader/cgi-bin
mv bootstrap /export/typeloader
cp -f html/* /export/typeloader
cp -f cgi/* /export/typeloader/cgi-bin
chmod +x /export/typeloader/cgi-bin/*.cgi
cp -f pysrc/* /export/typeloader/cgi-bin
echo "done."
echo ""

echo "Creating and configuring data input and output folders ..."
mkdir -p /downloads/bulk
mkdir -p /downloads/enabulk
mkdir -p /downloads/enafiles
mkdir -p /downloads/imgtbulk
mkdir -p /downloads/imgtfiles
mkdir -p /downloads/imgtinput
mkdir -p /downloads/imgtoutput
mkdir -p /downloads/xmlfiles
chown -R www-data /downloads
chgrp -R www-data /downloads
echo "done."
echo ""

echo "Getting Apache with TypeLoader going ..."
if /etc/init.d/apache2 restart > /dev/null 2>&1
then
    echo "done."
    echo ""
    ipaddress=`ifconfig | sed -En 's/127.0.0.1//;s/.*inet (addr:)?(([0-9]*\.){3}[0-9]*).*/\2/p'`
    echo "You can now access TypeLoader at http://localhost/typeloader/index.html on this machine."
    echo "From another machine on the network, TypeLoader can be accessed at http://"$ipaddress"/typeloader/index.html"
    echo ""
    echo ""
    echo "Go in Peace!"
    echo ""
else
    echo "failed."
    echo "**Error**There is a problem with Apache. Please contact the systems administrator."
    echo ""
    echo ""
fi
















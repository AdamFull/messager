#!/bin/sh

echo -e "\e[33mUPDATING CURENT PACKAGES\e[39m"
sudo apt-get update
sudo apt-get upgrade -y
 
# REMOVE OLD CORES
CORES=$(dpkg -l 'linux-*' | sed '/^ii/!d;/'"$(uname -r | sed "s/\(.*\)-\([^0-9]\+\)/\1/")"'/d;s/^[^ ]* [^ ]* \([^ ]*\).*/\1/;/[0-9]/!d' | head -n -1)
if [ "$CORES" != "" ]; then
    echo -e "\e[33mREMOVING OLD CORES\e[39m"
    sudo apt-get purge $(dpkg -l 'linux-*' | sed '/^ii/!d;/'"$(uname -r | sed "s/\(.*\)-\([^0-9]\+\)/\1/")"'/d;s/^[^ ]* [^ ]* \([^ ]*\).*/\1/;/[0-9]/!d' | head -n -1)
else
    echo -e "\e[33mOLD CORES DO NOT EXISTS\e[39m"
fi
# REMOVE UNNESESSARY PACKAGES
sudo apt-get autoremove -y
 
# REMOVE CONFIG FILES OF DELETED PACKAGES
CONFIG_COUNT=$(dpkg -l | awk '/^rc/ {print $2}' | wc -l)
if [ "$CONFIG_COUNT" -gt 0 ]; then
    echo -e "\e[33mREMOVING CONFIG FILES OF DELETED PACKAGES\e[39m"
    dpkg -l | awk '/^rc/ {print $2}' | sudo  xargs dpkg -P
else
    echo -e "\e[33mCONFIG FILES OF DELETED PACKAGES DO NOT EXISTS\e[39m"
fi
# CLEAN APT CACHE
echo -e "\e[33mCLEANING APT CACHE\e[39m"
sudo apt-get autoclean -y
sudo apt-get clean -y
 
# UPDATE GRUB
if [ "$CORES" != "" ]; then
    echo -e "\e[33mUPDATING GRUB\e[39m"
    sudo update-grub
fi

# echo -e "\e[33mREGOOTING\e[39m"
# sudo reboot

# UNLOCK CRASHED PACKAGES
# sudo dpkg --configure -a
# sudo apt-get clean
# sudo rm /var/lib/apt/lists/lock 

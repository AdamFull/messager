 
#!/bin/sh

sudo apt update
sudo apt upgrade -y
sudo apt install snapd -y

sudo add-apt-repository ppa:graphics-drivers/ppa
sudo apt update
sudo apt install nvidia-driver-430 libnvidia-gl-430 libnvidia-gl-430:i386
sudo apt install libvulkan1 libvulkan1:i386

sudo snap install snap-store
sudo snap install intellij-idea-ultimate --classic
sudo snap install pycharm-professional --classic
sudo snap install clion --classic

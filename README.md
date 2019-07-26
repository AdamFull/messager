# Messager

This project is a client in conjunction with the server.
A special feature is the freedom to choose a server, which guarantees privacy in the network. You can also start your server, which allows you to communicate with your friends freely, without fear of surveillance.

## Last release 0.4.1

- Added sending messages to offline users.

## Fixes

- Fixed bugs with downloading messages.
- Fixed bugs with upload that were not sent to the client.
- Fixed errors due to which access to the server from the application was not available.

### How to start server?

- First you need to install libraries for ```Python 3.6 (and higher)```. All necessary libraries are in ```requirements.txt```.
- After you need to run the file ```server_launcher.py```

### How to start client?

- First you need to install libraries for ```Python 3.6 (and higher)```. All necessary libraries are in ```requirements.txt```.
- After you need to run the file ```client_interface.py```. Test server: 8```4.201.170.33:9191``` (version 0.4 ,alpha , release)

###If you find an error, fill out the form, and send us an email.

## Used third-party libraries

- pycryptodome
- PyQt5
- autologging
- psutil
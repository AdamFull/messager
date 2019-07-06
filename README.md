# Messager

This project is a client in conjunction with the server.
A special feature is the freedom to choose a server, which guarantees privacy in the network. You can also start your server, which allows you to communicate with your friends freely, without fear of surveillance.

## Last release 0.3.2

- Fixed a delay in loading the interface when connecting.
- Fixed Log folder error in server.
- Fixed a bug when leaving the client with a partial connection to the server.
- Now the connection to the server has its own connection class.
- Added support for the command / server users to display users on the server.
- Authorization is implemented through RS encryption.
- The client folder "config" stores the encrypted private key and server information. Server data is taken depending on the current configuration of the ip: port.

## Used third-party libraries

- pycryptodome
- PyQt5
- autologging
# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'server_list.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_serverList(object):
    def setupUi(self, serverList):
        serverList.setObjectName("serverList")
        serverList.resize(339, 229)
        serverList.setMinimumSize(QtCore.QSize(339, 229))
        serverList.setMaximumSize(QtCore.QSize(339, 229))
        self.verticalLayout = QtWidgets.QVBoxLayout(serverList)
        self.verticalLayout.setObjectName("verticalLayout")
        self.server_list = QtWidgets.QListWidget(serverList)
        self.server_list.setObjectName("server_list")
        self.verticalLayout.addWidget(self.server_list)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.connect_btn = QtWidgets.QPushButton(serverList)
        self.connect_btn.setObjectName("connect_btn")
        self.horizontalLayout.addWidget(self.connect_btn)
        self.delete_btn = QtWidgets.QPushButton(serverList)
        self.delete_btn.setObjectName("delete_btn")
        self.horizontalLayout.addWidget(self.delete_btn)
        self.cancel_btn = QtWidgets.QPushButton(serverList)
        self.cancel_btn.setObjectName("cancel_btn")
        self.horizontalLayout.addWidget(self.cancel_btn)
        self.verticalLayout.addLayout(self.horizontalLayout)

        self.retranslateUi(serverList)
        QtCore.QMetaObject.connectSlotsByName(serverList)

    def retranslateUi(self, serverList):
        _translate = QtCore.QCoreApplication.translate
        serverList.setWindowTitle(_translate("serverList", "Server List"))
        self.connect_btn.setText(_translate("serverList", "Connect"))
        self.delete_btn.setText(_translate("serverList", "Delete"))
        self.cancel_btn.setText(_translate("serverList", "Cancel"))


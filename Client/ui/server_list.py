# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'server_list.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_dialog_layout(object):
    def setupUi(self, dialog_layout):
        dialog_layout.setObjectName("dialog_layout")
        dialog_layout.resize(354, 201)
        dialog_layout.setMinimumSize(QtCore.QSize(354, 201))
        dialog_layout.setMaximumSize(QtCore.QSize(354, 201))
        self.verticalLayout = QtWidgets.QVBoxLayout(dialog_layout)
        self.verticalLayout.setObjectName("verticalLayout")
        self.server_list = QtWidgets.QListWidget(dialog_layout)
        self.server_list.setObjectName("server_list")
        self.verticalLayout.addWidget(self.server_list)
        self.buttons_layout = QtWidgets.QHBoxLayout()
        self.buttons_layout.setObjectName("buttons_layout")
        self.connect_btn = QtWidgets.QPushButton(dialog_layout)
        self.connect_btn.setObjectName("connect_btn")
        self.buttons_layout.addWidget(self.connect_btn)
        self.remove_btn = QtWidgets.QPushButton(dialog_layout)
        self.remove_btn.setObjectName("remove_btn")
        self.buttons_layout.addWidget(self.remove_btn)
        self.cancel_btn = QtWidgets.QPushButton(dialog_layout)
        self.cancel_btn.setObjectName("cancel_btn")
        self.buttons_layout.addWidget(self.cancel_btn)
        self.verticalLayout.addLayout(self.buttons_layout)

        self.retranslateUi(dialog_layout)
        QtCore.QMetaObject.connectSlotsByName(dialog_layout)

    def retranslateUi(self, dialog_layout):
        _translate = QtCore.QCoreApplication.translate
        dialog_layout.setWindowTitle(_translate("dialog_layout", "Select server"))
        self.connect_btn.setText(_translate("dialog_layout", "Connect"))
        self.remove_btn.setText(_translate("dialog_layout", "Remove"))
        self.cancel_btn.setText(_translate("dialog_layout", "Cancel"))


from PyQt5 import QtWidgets, QtGui, QtCore
from ui.main_window import Ui_Messager
from ui.connect_dialog import Ui_AddServer
from threading import Thread
from client import Client, STATEMENT
from client_settings import ClientSetting
from sys import stdout

# pyuic5 mainui.ui -o UI.py

class Connect(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(Connect, self).__init__(parent)
        self.ui = Ui_AddServer()
        self.ui.setupUi(self)

        self.ui.server_ip.setText('localhost')
        self.ui.server_port.setValue(9191)
        self.ui.username.setText('willson')
        self.ui.nickname.setText('nagibator228')
        self.ui.password.setText('g159753H')
        self.ui.confirm.setText('g159753H')

        self.ui.connect_brn.clicked.connect(self.connect)
        self.ui.cancel_btn.clicked.connect(self.close)
    
    def connect(self):
        if self.ui.password.text() == self.ui.confirm.text():
            self.server_ip = self.ui.server_ip.text()
            self.port = self.ui.server_port.value()
            self.username = self.ui.username.text()
            self.nickname = self.ui.nickname.text()
            self.password = self.ui.password.text()
            self.accept()

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, parent = None):
        super(MainWindow, self).__init__(parent)
        self.ui = Ui_Messager()
        self.ui.setupUi(self)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        self.client = Client()

        self.ui.actionConnect.triggered.connect(self.connect)

        self.ui.statusbar.showMessage("Disconnected.")
    
    def run_connection(self):
        client_thread = Thread(target=self.client.run)
        client_thread.start()
        self.watchdog_thread = Thread(target=self.watchdog)
        self.watchdog_thread.start()
    
    
    def watchdog(self):
        while True:
            c_state = self.client.STATE
            c_msg = self.client.current_message
            if c_state == STATEMENT().CONNECTING:
                self.ui.statusbar.showMessage(c_msg)
            elif c_state == STATEMENT().CONNECTED:
                pass
            elif c_state == STATEMENT().DISCONNECTED:
                break
            elif c_state == STATEMENT().VERIFICATION:
                key, ok = self.inputDialog('Verification', 'Enter verification key: ')
                if key and ok:
                    self.client.send_verification_key(str(key))
    
    def inputDialog(self, windName, textName):
        return QtWidgets.QInputDialog.getText(self, windName, textName)

    def connect(self):
        dialog = Connect()
        if dialog.exec_()==QtWidgets.QDialog.Accepted:
            self.client.setting.server_ip = dialog.server_ip
            self.client.setting.port = dialog.port
            self.client.setting.username = dialog.username
            self.client.setting.nickname = dialog.nickname
            self.client.setting.password = dialog.password
            self.client.setting.generate_rsa()
            self.client.setting.save()
        self.client.setting.load()
        self.run_connection()


if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    application = MainWindow()
    application.show()
    app.exec()
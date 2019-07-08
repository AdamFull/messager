from PyQt5 import QtWidgets, QtGui, QtCore
from ui.main_window import Ui_Messager
from ui.connect_dialog import Ui_AddServer
from ui.server_list import Ui_serverList
from threading import Thread
from client import Client, STATEMENT, Observer, Subject
from client_settings import ClientSetting
import time

# pyuic5 main_window.ui -o main_window.py
# pyuic5 connect_dialog.ui -o connect_dialog.py

class ObserverWorker(QtCore.QObject):
    message = QtCore.pyqtSignal(object)
    status = QtCore.pyqtSignal(object)
    verivication = QtCore.pyqtSignal()
    server = QtCore.pyqtSignal(object, object)
    rooms = QtCore.pyqtSignal(object)
    users = QtCore.pyqtSignal(object)

    def recvMessage(self, msg):
        self.message.emit(msg)
    
    def recvStatus(self, msg):
        self.status.emit(msg)
    
    def recvVerif(self):
        self.verivication.emit()
    
    def recvServer(self, msg):
        self.server.emit(msg, QtCore.Qt.AlignCenter)

    def recvRooms(self, msg):
        self.rooms.emit(msg)
    
    def recvUsers(self, msg):
        self.users.emit(msg)


class ConcreteObserver(Observer):
    def __init__(self):
        self.observer_worker = ObserverWorker()
        self.need_update = True
    
    def update(self, subject:Subject) -> None:
        c_state = subject._STATE
        c_msg = subject._CURRENT_MESSAGE
        c_infotype = subject._INFOTYPE
        if c_infotype == "stat":
            self.observer_worker.recvStatus(c_msg)
        elif c_infotype == "msg":
            self.observer_worker.recvMessage(c_msg)
        elif c_infotype == "srv":
            self.observer_worker.recvServer(c_msg)
        elif c_infotype == "rms":
            self.observer_worker.recvRooms(c_msg)
        elif c_infotype == "usrs":
            self.observer_worker.recvUsers(c_msg)

        if c_state == 2:
            self.observer_worker.recvVerif()
        if c_state == 1 and self.need_update:
            self.need_update = False
            subject.server_command("server rooms")


class Connect(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(Connect, self).__init__(parent)
        self.ui = Ui_AddServer()
        self.ui.setupUi(self)

        self.ui.server_ip.setText('localhost')
        self.ui.server_port.setValue(9191)
        self.ui.nickname.setText('nagibator228')
        self.ui.password.setText('g159753H')
        self.ui.confirm.setText('g159753H')

        self.ui.connect_btn.clicked.connect(self.connect)
        self.ui.cancel_btn.clicked.connect(self.close)
        self.ui.new_tab_btn.clicked.connect(self.new_window)
    
    def new_window(self):
        print("SOON")
        pass

    def connect(self):
        if self.ui.password.text() == self.ui.confirm.text():
            self.server_ip = self.ui.server_ip.text()
            self.port = self.ui.server_port.value()
            self.nickname = self.ui.nickname.text()
            self.password = self.ui.password.text()
            self.accept()

class ServerList(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(ServerList, self).__init__(parent)
        self.ui = Ui_serverList()
        self.ui.setupUi(self)
        self.load()
    
    def load(self):
        pass

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, parent = None):
        super(MainWindow, self).__init__(parent)
        self.ui = Ui_Messager()
        self.ui.setupUi(self)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        # Backend client
        self.client: Client = Client()
        self.observer: ConcreteObserver = ConcreteObserver()
        self.observer.observer_worker.status.connect(self.ui.statusbar.showMessage)
        self.observer.observer_worker.message.connect(self.recvMessage)
        self.observer.observer_worker.verivication.connect(self.verification_input)
        self.observer.observer_worker.server.connect(self.recvMessage)
        self.observer.observer_worker.rooms.connect(self.loadRooms)
        self.observer.observer_worker.users.connect(self.loadUsers)
        self.client.attach(self.observer)

        self.thread__ = Thread(target=self.client.run)

        # Menu actions
        self.ui.actionConnect.triggered.connect(self.connect)
        self.ui.actionDisconnect_from_current.triggered.connect(self.disconnect_)
        self.ui.actionServer_list.triggered.connect(print)

        # Other actions...

        # UI actions
        self.ui.send_message.clicked.connect(self.sendMessage)
        self.ui.room_list.itemDoubleClicked.connect(self.changeRoom)
        # self.ui.message_box.textEdited.connect() #If text edited...
        self.ui.message_box.returnPressed.connect(self.sendMessage)

        # UI defaults
        self.ui.statusbar.showMessage("Disconnected.")
        self.ui.chat_list.setWordWrap(True)
        self.ui.room_list.setWordWrap(True)
    
    def sendMessage(self):
        msg = self.ui.message_box.text()
        if msg and self.client.isLogined:
            self.client.send(msg)
            self.recvMessage(msg, QtCore.Qt.AlignRight)
            self.ui.message_box.setText("")
    
    def changeRoom(self, item):
        self.ui.chat_list.clear()
        self.client.server_command("server chroom %s" % item.text())

    def recvMessage(self, msg, align=QtCore.Qt.AlignLeft):
        item = QtWidgets.QListWidgetItem(msg)
        item.setTextAlignment(align)
        self.ui.chat_list.addItem(item)
        self.ui.chat_list.scrollToItem(item)
    
    def loadUsers(self, msg):
        print(msg)

    def verification_input(self):
        key, ok = QtWidgets.QInputDialog.getText(self, 'Verification', 'Enter verification key: ')
        if key and ok:
            self.client.send_verification_key(str(key))
    
    def loadRooms(self, msg:str):
        rooms = msg.split(',')
        self.ui.room_list.clear()
        for room in rooms:
            item = QtWidgets.QListWidgetItem(room)
            self.ui.room_list.addItem(item)
            
    def disconnect_(self) -> None:
        if self.client.isLogined:
            self.client.disconnect()
            self.thread__.join()

    def run_connection(self):
        self.thread__ = Thread(target=self.client.run)
        self.thread__.start()

    def connect(self):
        dialog = Connect()
        if dialog.exec_()==QtWidgets.QDialog.Accepted:
            self.client.setting.server_ip = dialog.server_ip
            self.client.setting.port = dialog.port
            self.client.setting.nickname = dialog.nickname
            self.client.setting.password = dialog.password
            self.client.setting.generate_rsa()
            self.client.setting.save()
        else:
            return
        self.client.setting.load()
        self.run_connection()
    
    def close(self) -> None:
        self.client.detach(self.observer)
        self.client.close()


if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    application = MainWindow()
    application.show()
    app.exec()
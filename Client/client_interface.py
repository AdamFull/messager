from PyQt5 import QtWidgets, QtGui, QtCore, QtMultimedia
from ui.main_window import Ui_Messager
from ui.connect_dialog import Ui_AddServer
from ui.server_list import Ui_dialog_layout
from threading import Thread
from client import Client, STATEMENT, Observer, Subject
import time
from random import randrange as rr

# pyuic5 main_window.ui -o main_window.py
# pyuic5 connect_dialog.ui -o connect_dialog.py

__version__ = [0, 4, 1, "alpha", "release"]

class ObserverWorker(QtCore.QObject):
    data = QtCore.pyqtSignal(object)

    def recvData(self, msg):
        self.data.emit(msg)

class ConcreteObserver(Observer):
  
    def __init__(self):
        self.observer_worker = ObserverWorker()
        self.need_update = True
    
    def update(self, subject:Subject) -> None:
        c_state = subject._STATE
        c_msg = subject._CURRENT_MESSAGE
        self.observer_worker.recvData(c_msg)

        if c_state == 2:
            self.observer_worker.recvData({"verification": None})


class Connect(QtWidgets.QDialog):
    def __init__(self, client, parent=None):
        super(Connect, self).__init__(parent)
        self.ui = Ui_AddServer()
        self.ui.setupUi(self)

        self.client = client

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
            self.data = [self.ui.server_ip.text(), self.ui.server_port.value(), self.ui.nickname.text(), self.ui.password.text()]
            self.accept()

class ServerList(QtWidgets.QDialog):
    def __init__(self, client: Client, parent=None):
        super(ServerList, self).__init__(parent)
        self.ui = Ui_dialog_layout()
        self.ui.setupUi(self)

        self.client: Client = client
        self.configurations = self.client.setting.get_configurations()

        self.load_list()
        
        self.ui.connect_btn.clicked.connect(self.load)
        self.ui.remove_btn.clicked.connect(self.remove)
        self.ui.cancel_btn.clicked.connect(self.close)
    
    def load_list(self):
        self.ui.server_list.clear()
        for config in self.configurations:
            item = QtWidgets.QListWidgetItem('   '.join([str(x) for x in config[1:len(config)-2]]))
            item.setData(QtCore.Qt.UserRole, config[1:len(config)-1])
            item.setTextAlignment(QtCore.Qt.AlignCenter)
            self.ui.server_list.addItem(item)

    def remove(self):
        pass

    def load(self):
        c_item = self.ui.server_list.currentItem().data(QtCore.Qt.UserRole)
        if c_item:
            self.data = c_item
            self.accept()

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, parent = None):
        super(MainWindow, self).__init__(parent)
        self.ui = Ui_Messager()
        self.ui.setupUi(self)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        # Backend client
        self.client: Client = Client()
        self.observer: ConcreteObserver = ConcreteObserver()
        self.observer.observer_worker.data.connect(self.update)
        self.client.attach(self.observer)

        self.thread__ = Thread(target=self.client.run)

        self.current_chat = None

        # Menu actions
        self.ui.actionConnect.triggered.connect(self.connect)
        self.ui.actionDisconnect_from_current.triggered.connect(self.disconnect_)
        self.ui.actionServer_list.triggered.connect(self.server_list)

        # Other actions...

        # UI actions
        self.ui.send_message.clicked.connect(self.sendMessage)
        self.ui.room_list.itemClicked.connect(self.changeRoom)
        # self.ui.message_box.textEdited.connect() #If text edited...
        self.ui.message_box.returnPressed.connect(self.sendMessage)
        self.ui.search_t.textEdited.connect(self.findChat)
        self.ui.search_t.setEnabled(False)
        self.ui.open_sb_btn.clicked.connect(self.create_chat)

        # UI defaults
        self.ui.statusbar.showMessage("Disconnected.")
        self.ui.chat_list.setWordWrap(True)
        self.ui.room_list.setWordWrap(True)
        self.ui.room_list.setIconSize(QtCore.QSize(45, 45))
    
    def sendMessage(self):
        msg = self.ui.message_box.text()
        if msg and self.client.isLogined and self.client.current_chat:
            self.client.send(msg)
            self.recvMessage(msg, QtCore.Qt.AlignRight)
            self.ui.message_box.setText("")
    
    def recvMessage(self, msg, chat, align=QtCore.Qt.AlignLeft):
        if chat == self.client.current_chat:
            item = QtWidgets.QListWidgetItem(msg)
            item.setTextAlignment(align)
            self.ui.chat_list.addItem(item)
            self.ui.chat_list.scrollToItem(item)
    
    def findChat(self):
        text = self.ui.search_t.text()
        if self.client.isLogined:
            if text: 
                self.client.find_request(text)
            else:
                self.client.find_request(None)
    
    def loadRooms(self, msg):
        self.ui.room_list.clear()
        for room in msg:
            item = QtWidgets.QListWidgetItem(room)
            item.setSizeHint(QtCore.QSize(0, 50))
            item.setTextAlignment(QtCore.Qt.AlignLeft)
            pixmap = QtGui.QPixmap(45, 45)
            pixmap.fill(QtGui.QColor(rr(0, 255), rr(0, 255), rr(0, 255)))
            item.setIcon(QtGui.QIcon(pixmap))
            self.ui.room_list.addItem(item)

    def update(self, data: dict, loading=False):
        self.ui.search_t.setEnabled(True)
        keys = data.keys()
        if "msg" in keys:
            if not loading:
                self.client.setting.recv_message(data["chat"], data)
                QtMultimedia.QSound("/audio/msg.wav").play()
            self.recvMessage("[%s][%s]: %s" % (data["time"], data["nickname"], data["msg"]), 
                            data["chat"],
                            QtCore.Qt.AlignRight if self.client.setting.nickname == data["nickname"] else QtCore.Qt.AlignLeft)
        elif "info" in keys:
            print(data["info"])
        elif "users" in keys:
            print(data["users"])
        elif "chats" in keys:
            self.loadRooms(data["chats"])
        elif "status" in keys:
            self.ui.statusbar.showMessage(data["status"])
        elif "verification" in keys:
            self.verification_input()
        else:
            print(data)
    
    def changeRoom(self, item):
        self.ui.chat_list.clear()
        self.client.change_chat(item.text())
        messages = self.client.setting.load_chat(item.text())
        if messages:
            for message in messages:
                self.update({"nickname": message[1], "msg": message[2], "chat": message[3], "time": message[4], "date": message[5]}, True)

    def verification_input(self):
        key, ok = QtWidgets.QInputDialog.getText(self, 'Verification', 'Enter verification key: ')
        if key and ok:
            self.client.send_verification_key(str(key))
    
    def create_chat(self):
        if self.client.isLogined:
            key, ok = QtWidgets.QInputDialog.getText(self, 'Change chat name', 'Chat name: ')
            if key and ok:
                self.client.create_chat(str(key))
            
    def disconnect_(self) -> None:
        if self.client.isLogined:
            self.client.disconnect()
            self.ui.chat_list.clear()
            self.ui.room_list.clear()
    
    def server_list(self):
        dialog = ServerList(self.client)
        if dialog.exec_()==QtWidgets.QDialog.Accepted:
            self.client.setting.load(dialog.data)
        else:
            return
        self.run_connection()

    def run_connection(self):
        self.thread__ = Thread(target=self.client.run)
        self.thread__.start()

    def connect(self):
        dialog = Connect(self.client)
        if dialog.exec_()==QtWidgets.QDialog.Accepted:
            print(dialog.data)
            self.client.setting.load(dialog.data)
        else:
            return
        self.run_connection()
    
    def close(self) -> None:
        self.client.detach(self.observer)
        self.client.close()


if __name__ == "__main__":
    print("VERSION: ", __version__)
    app = QtWidgets.QApplication([])
    application = MainWindow()
    application.show()
    app.exec()
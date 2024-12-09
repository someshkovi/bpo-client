import sys
import json
import requests
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout,
      QHBoxLayout, QLabel, QLineEdit, QTextEdit,
        QPushButton, QTabWidget, QMainWindow, QInputDialog, QMenu)

import urllib3
urllib3.disable_warnings()

TOKEN_URI = '/tron/api/v1/tokens'
GET_IFD_L3_CONTAINTER_URI = '/bpocore/market/api/v1/resources?exactTypeId=ifd.v6.resourceTypes.L3ServiceOperationContainer'
POST_IFD_OP_URI = '/bpocore/market/api/v1/resources/{L3_SERVICE_CONTAINER_ID}/operations'
GET_IFD_OP_STATUS_URI = '/bpocore/market/api/v1/resources/{RESO_ID}/operations/{OPER_ID}'


class ApiClient(QMainWindow):
    def __init__(self):
        super().__init__()
        # self.initUI()

        self.setWindowTitle("API Client")
        self.setMinimumSize(800, 600)

        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tabs.customContextMenuRequested.connect(self.show_tab_context_menu)
        self.setCentralWidget(self.tabs)

        self.load_state()

        # Menu for adding new tabs
        self.menu = self.menuBar().addMenu("File")
        self.menu.addAction("New Tab", self.add_tab)
        self.menu.addSeparator()
        self.menu.addAction("Exit", self.close)

    def add_tab(self, state=None):
        tab = QWidget()
        layout = QVBoxLayout()

        # Server, Username, and Password input
        server_layout = QHBoxLayout()
        self.server = QLabel('SERVER:')
        self.server_input = QLineEdit()
        # self.server_input.setMaximumSize(100, 20)
        # self.server.setAlignment(Qt.AlignmentFlag.AlignRight)
        # self.server_input.setAlignment(Qt.AlignmentFlag.AlignRight)
        server_layout.addWidget(self.server)
        server_layout.addWidget(self.server_input)

        self.user_name = QLabel('user name:')
        self.user_name_input = QLineEdit()
        server_layout.addWidget(self.user_name)
        server_layout.addWidget(self.user_name_input)

        self.password = QLabel('password:')
        self.password_input = QLineEdit()
        server_layout.addWidget(self.password)
        server_layout.addWidget(self.password_input)

        self.submit_button = QPushButton('Submit')
        self.submit_button.clicked.connect(self.make_api_calls)
        server_layout.addWidget(self.submit_button)

        layout.addLayout(server_layout)

        # Headers input
        # self.headers_label = QLabel('Headers (JSON format):')
        # self.headers_input = QTextEdit()
        # layout.addWidget(self.headers_label)
        # layout.addWidget(self.headers_input)

        # Response display
        response_layout = QHBoxLayout()
        self.payload_label = QLabel('Payload:')
        self.payload_input = QTextEdit()
        self.payload_input.setFontPointSize(12)
        response_layout.addWidget(self.payload_label)
        response_layout.addWidget(self.payload_input)

        self.response_label_2 = QLabel('Response 2:')
        self.response_display_2 = QTextEdit()
        self.response_display_2.setReadOnly(True)
        self.response_display_2.setFontPointSize(12)
        response_layout.addWidget(self.response_label_2)
        response_layout.addWidget(self.response_display_2)

        layout.addLayout(response_layout)

        # Retry button for the last API call
        self.retry_button = QPushButton('Retry Last Call')
        self.retry_button.clicked.connect(self.retry_last_call)
        self.retry_button.setEnabled(False)
        layout.addWidget(self.retry_button)

        tab.setLayout(layout)
        self.tabs.addTab(tab, f"Tab {self.tabs.count() + 1}")

        # Restore state if provided
        if state:
            self.server.setText(state.get("url", ""))
            # method_combobox.setCurrentText(state.get("method", "GET"))
            # headers_text.setPlainText(state.get("headers", ""))
            # payload_text.setPlainText(state.get("payload", ""))
            # body_text.setPlainText(state.get("body", ""))

    def save_state(self):
        state = []
        for i in range(self.tabs.count()):
            tab = self.tabs.widget(i)
            # url_entry = tab.findChild(QLineEdit)
            # method_combobox = tab.findChild(QComboBox)
            # headers_text = tab.findChild(QTextEdit, "Headers (JSON) - Optional")
            # payload_text = tab.findChild(QTextEdit, "Payload (JSON) - Optional")
            # body_text = tab.findChild(QTextEdit, "Body (JSON) [POST only]")

            # tab_state = {
            #     "url": url_entry.text(),
            #     "method": method_combobox.currentText(),
            # }
            # if headers_text:
            #     tab_state["headers"] = headers_text.toPlainText()
            # if payload_text:
            #     tab_state["payload"] = payload_text.toPlainText()
            # if body_text:
            #     tab_state["body"] = body_text.toPlainText()

            # state.append(tab_state)

        with open("client_state.json", "w") as f:
            json.dump(state, f, indent=2)

    def load_state(self):
        # try:
        #     with open("client_state.json", "r") as f:
        #         state = json.load(f)
        #         for tab_state in state:
        #             self.add_tab(tab_state)
        # except (FileNotFoundError, json.JSONDecodeError):
        #     self.add_tab()

        self.add_tab() #TODO: Implement loading state from JSON file


    def closeEvent(self, event):
        self.save_state()
        event.accept()

    def close_tab(self, index):
        self.tabs.removeTab(index)

    def show_tab_context_menu(self, position):
        context_menu = QMenu()
        rename_action = context_menu.addAction("Rename Tab")
        close_action = context_menu.addAction("Close Tab")

        action = context_menu.exec(self.tabs.mapToGlobal(position))

        if action == rename_action:
            self.rename_tab()
        elif action == close_action:
            self.close_tab(self.tabs.currentIndex())

    def rename_tab(self):
        index = self.tabs.currentIndex()
        new_name, ok = QInputDialog.getText(self, "Rename Tab", "Enter new tab name:")
        if ok and new_name:
            self.tabs.setTabText(index, new_name)


    def initUI(self):
        self.setWindowTitle('API Client')
        self.setMinimumSize(800, 600)

        # self.setLayout(layout)

        # Variables to store token and headers for retry
        self.token = None
        self.headers_dict = None

    def get_token_call(self):
        url = self.server_url + TOKEN_URI
        username = self.user_name_input.text() or 'admin'
        password = self.password_input.text() or 'adminpw'
        payload_dict = {'username': username, 'password': password}
        response1 = requests.post(url, headers={}, data=payload_dict, timeout=10, verify=False)
        response1_data = response1.json()
        self.token = response1_data.get('token')
        print(f'Token obtained: {self.token}')
        return self.token
    
    def get_ifd_l3_container_call(self)->str:
        url = self.server_url + GET_IFD_L3_CONTAINTER_URI
        headers_dict = {'Authorization': f'Bearer {self.token}'}
        response = requests.get(url, headers=headers_dict, timeout=10, verify=False)
        response_data = response.json()
        print(response_data)
        print(f'L3 service container ID obtained: {response_data.get("items")[0]["id"]}')
        return response_data.get('items')[0]['id']

    def post_ifd_op_call(self, l3_service_container_id: str, payload: dict)->str:
        url = self.server_url + POST_IFD_OP_URI.format(L3_SERVICE_CONTAINER_ID=l3_service_container_id)
        headers_dict = {'Authorization': f'Bearer {self.token}', 
                        'Content-Type': 'application/json'}
        response = requests.post(url, headers=headers_dict, data=json.dumps(payload), timeout=120, verify=False)
        response_data = response.json()
        print(f'Operation ID obtained: {response_data}')
        return response_data
    
    def get_ifd_op_status_call(self, reso_id: str, oper_id: str)->str:
        url = self.server_url + GET_IFD_OP_STATUS_URI.format(RESO_ID=reso_id, OPER_ID=oper_id)
        headers_dict = {'Authorization': f'Bearer {self.token}',
                        'Content-Type': 'application/json'}
        response = requests.get(url, headers=headers_dict, timeout=10, verify=False)
        response_data = response.json()
        return response_data


    def display_response(self, response, response_text, clear_inputs=False):
        try:
            if clear_inputs and response.get('inputs'):
                response.pop('inputs')
            formatted_response = json.dumps(response, indent=4)
            # html_formatted_json = f"<pre>{formaatted_response}</pre>"
            # response_text.setHtml(html_formatted_json)
            response_text.setPlainText(formatted_response)
        except json.JSONDecodeError as e:
            print(f'getting json decode error {e}')
            formatted_response = str(response)
            response_text.setPlainText(formatted_response)

    def make_api_calls(self):
        self.response_display_2.setText('')
        payload = self.payload_input.toPlainText()
        if self.server_input.text():
            server_ip = self.server_input.text()
        else:
            server_ip = 'hac-skovi-1'
            self.server_input.setText(server_ip)

        self.server_url = f'https://{server_ip}'
        try:
            self.get_token_call()
            self.l3_container = self.get_ifd_l3_container_call()
            post_call_response = self.post_ifd_op_call(self.l3_container, json.loads(payload))
            self.reso_id = post_call_response.get('resourceId')
            self.oper_id = post_call_response.get('id')
            self.response_display_2.setText(str(post_call_response))
            # Check the status of the last call
            response4 = self.get_ifd_op_status_call(self.reso_id, self.oper_id)
            # self.response_display_2.setText(str(response4))
            self.display_response(response4, self.response_display_2, clear_inputs=True)
            # Enable retry button
            self.retry_button.setEnabled(True)

        except requests.RequestException as e:
            self.response_display_2.setText(f"API request failed: {str(e)}")
            # self.response_display_2.setText("")
            self.retry_button.setEnabled(False)

    def retry_last_call(self):
        try:
            self.response_display_2.setText('')
            response_data = self.get_ifd_op_status_call(self.reso_id, self.oper_id)
            # self.response_display_2.setText(str(response_data))
            self.display_response(response_data, self.response_display_2, clear_inputs=True)
        except requests.RequestException as e:
            self.response_display_2.setText(f"Retry API request failed: {str(e)}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    client = ApiClient()
    client.resize(800, 600)
    client.show()
    sys.exit(app.exec())
import socket

from p2p.connection_manager_4_edge import ConnectionManager4Edge

STATE_INIT = 0
STATE_ACTIVE = 1
STATE_SHUTTING_DOWN = 2

class ClientCore:
    def __init__(self, my_port=50082, core_node_host=None, core_node_port=None):
        self.client_state = STATE_INIT
        print('Initializeing server...')
        self.my_ip = self.__get_myip()
        self.my_port = my_port
        print('Server IP address is set to ...', self.my_ip)
        print('Server Port is set to ...', self.my_port)
        self.cm = ConnectionManager4Edge(self.my_ip, self.my_port,
                core_node_host, core_node_port)

    def start(self):
        self.client_state = STATE_ACTIVE
        self.cm.start()
        self.cm.connect_to_core_node()

    def shutdown(self):
        self.server_state = STATE_SHUTTING_DOWN
        print('Shutdown edge node...')
        self.cm.connection_close()

    def get_my_current_state(self):
        return self.server_state

    def __get_myip(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        return s.getsockname()[0]

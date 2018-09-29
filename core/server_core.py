STATE_INIT = 0
STATE_STANDBY = 1
STATE_CONNECTED_TO_NETWORK = 2
STATE_SHUTTING_DOWN = 3

import socket
from p2p.connection_manager import ConnectionManager
from p2p.my_protocol_message_handler import (
        MyProtocolMessageHandler,
        SEND_TO_ALL_EDGE,
        SEND_TO_ALL_PEER
        )
from p2p.message_manager import (
        MessageManager,
        MSG_NEW_TRANSACTION,
        MSG_NEW_BLOCK,
        RSP_FULL_CHAIN,
        MSG_ENHANCED,
        )

class ServerCore:
    def __init__(self, my_port=50082, core_node_host=None, core_node_port=None):
        self.server_state = STATE_INIT
        print('Initializeing server...')
        self.my_ip = self.__get_myip()
        self.my_port = my_port
        print('Server IP address is set to ...', self.my_ip)
        print('Server Port is set to ...', self.my_port)
        self.cm = ConnectionManager(self.my_ip, self.my_port, self.__handle_message)
        self.core_node_host = core_node_host
        self.core_node_port = core_node_port
        self.mpmh = MyProtocolMessageHandler()
        self.my_protocol_message_store = []

    def start(self):
        self.server_state = STATE_STANDBY
        self.cm.start()

    def join_network(self):
        if self.core_node_host is not None:
            self.server_state = STATE_CONNECTED_TO_NETWORK
            self.cm.join_network(self.core_node_host, self.core_node_port)
        else:
            print('This server is runnning as Genesis Nore Node...')

    def shutdown(self):
        self.server_state = STATE_SHUTTING_DOWN
        print('Shutdown server...')
        self.cm.connection_close()

    def get_my_current_state(self):
        return self.server_state

    def __get_myip(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        return s.getsockname()[0]

    def __handle_message(self, msg, peer=None):
        """
        ConnectionManagerに引き渡すコールバックの中身
        """
        print('received message!!!!!!!!!!!!!!!!', msg, peer)
        if peer is not None:
            print('peer is not None')
            pass
            # TODO: 現状はMSG_REQUEST_FULL_CHAINの場合しかこの処理には入らない
            # とりあえず口だけ作る
        else:
            cmd = msg[2]
            if cmd == MSG_NEW_TRANSACTION:
                # TODO: 新規transactionを登録する処理を呼び出す
                pass
            elif cmd == MSG_NEW_BLOCK:
                # TODO: 新規ブロックを検証する処理を呼び出す
                pass
            elif cmd == RSP_FULL_CHAIN:
                # TODO: ブロックチェーン送信要求に応じて返却されたブロックチェーンを検証する処理を呼び出す
                pass
            elif cmd == MSG_ENHANCED:
                print('received enhanced message', msg[4])
                # P2P Networkを単なるトランスポートとして使っているアプリケーションが独自拡張したメッセージを処理する
                
                # 重複チェック
                # ここで同じメッセージを送らないようにしないと永遠と送り続けるループに入ってしまう
                current_message = self.my_protocol_message_store
                print('received messages', current_message)
                has_same = False
                if not msg[4] in current_message:
                    self.my_protocol_message_store.append(msg[4])
                    self.mpmh.handle_message(msg[4], self.__core_api)

    def __core_api(self, request, message):
        """
        MyProtocolMessageHandlerで呼び出すための拡張関数群
        """
        msg_type = MSG_ENHANCED

        if request == SEND_TO_ALL_EDGE:
            print('Sending all edge...')
            new_message = self.cm.get_message_text(msg_type, message)
            self.cm.send_msg_to_all_edge(new_message)
            return 'ok'
        elif request == SEND_TO_ALL_PEER:
            new_message = self.cm.get_message_text(msg_type, message)
            self.cm.send_msg_to_all_peer(new_message)
            return 'ok'
        elif request == 'api_type':
            return 'server_core_api'


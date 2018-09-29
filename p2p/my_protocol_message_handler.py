import json

SEND_TO_ALL_PEER = 'send_message_to_all_peer'
SEND_TO_ALL_EDGE = 'send_message_to_all_edge'

PASS_TO_CLIENT_APP = 'pass_message_to_client_application'

# 独自に拡張したENHANCEDメッセージの処理や生成を担当する
class MyProtocolMessageHandler(object):
    def __init__(self):
        print('Initializeing MyProtocolMessageHandler...')

    def handle_message(self, msg, api):
        """
        受け取ったメッセージを自分がCoreノードならブロードキャスト
        Edgeならコンソールに出力することでメッセンジャーを作る
        params:
            msg : 拡張プロトコルで送られてきたJSON形式のメッセージ
            api : ServerCore(or ClientCore）側で用意されているAPI呼び出しのためのコールバック
            api(param1, param2) という形で利用する
        """
        print('MyProtocolMessageHandler received: ', msg)
        msg = json.loads(msg)

        my_api = api('api_type', None)
        print('my_api: ', my_api)
        if my_api == 'server_core_api':
            print('Bloadcasting...', json.dumps(msg))
            api(SEND_TO_ALL_PEER, json.dumps(msg))
            api(SEND_TO_ALL_EDGE, json.dumps(msg))
        else:
            api(PASS_TO_CLIENT_APP, msg)

        return

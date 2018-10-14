import threading

class CoreNodeList:
    def __init__(self):
        self.lock = threading.Lock()
        self.list = set()

    def add(self, peer):
        """
        Core ノードをリストに追加する
        """
        with self.lock:
            print('Adding peer: ', peer)
            self.list.add((peer))
            print('Current Core List: ', self.list)

    def remove(self, peer):
        """
        離脱したと判断されるCoreノードをリストから削除する
        """
        with self.lock:
            if peer in self.list:
                print('Removing peer: ', peer)
                self.list.remove(peer)
                print('Current Core list: ', self.list)

    def overwrite(self, new_list):
        """
        複数のpeerの接続状況確認を行ったあとで一括での上書き処理をする場合
        """
        with self.lock:
            print('core node list will be going to overwrite')
            self.list = new_list
            print('Current Core list: ', self.list)

    def get_list(self):
        """
        現在接続状態にあるPeerの一覧を返却
        """
        return self.list

    def has_this_peer(self, peer):
        """
        与えられたpeerがリストに含まれているかをチェックする
        """
        return peer in self.list

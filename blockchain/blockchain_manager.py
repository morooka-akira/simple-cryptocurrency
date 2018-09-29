import binascii
import hashlib
import json
import threading

class BlockchainManager:
    def __init__(self, genesis_block):
        print('Initializing BlockchainManager...')
        self.chain = []
        self.lock = threading.Lock()
        self.__set_my_genesis_block(genesis_block)

    def __set_my_genesis_block(self, block):
        self.genesis_block = block
        self.chain.append(block)
    
    def set_new_block(self, block):
        with self.lock:
            self.chain.append(block)

    def _get_double_sha256(self, message):
        # hashlibはUnicode型に対応していないのでencodeの必要がある for Python3
        return hashlib.sha256(hashlib.sha256(message.encode('utf-8')).digest()).digest()

    def get_hash(self, block):
        """
        正当性確認に使うためブロックのハッシュ値を取る
        :param block: Block
        """
        # キーの順番による不整合が発生しないようにソート
        block_json = json.dumps(block, sort_keys=True)
        return binascii.hexlify(self._get_double_sha256(block_json)).decode('ascii')

    def is_valid(self, chain):
        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = self.chain[current_index]
            if block['previous_block'] != self.get_hash(last_block):
                return False

            last_block = block
            current_index += 1
        return True

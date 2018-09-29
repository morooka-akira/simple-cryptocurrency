from time import time
import json

class Block:
    def __init__(self, transaction, previous_block_hash):
        self.timestamp = time()
        self.transaction = transaction
        self.previous_block = previous_block_hash

    def to_dict(self):
        d = {
                'timestamp' : self.timestamp,
                'transaction' : json.dumps(self.transaction),
                'previous_block' : self.previous_block
            }
        return d

class GenesisBlock(Block):
    """
    前方にブロックを持たない始原のブロック
    """
    def __init__(self):
        super().__init__(transaction='abc', previous_block_hash=None)

    def to_dict(self):
        d = {
                'transaction' : self.transaction,
                'genesis_block': True
            }
        return d

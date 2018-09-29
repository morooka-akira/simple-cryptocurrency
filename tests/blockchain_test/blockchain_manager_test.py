import hashlib
import binascii
import json

from blockchain.blockchain_manager import BlockchainManager
from blockchain.block import Block
from blockchain.block import GenesisBlock

def test_set_new_block():
    genesis = GenesisBlock()
    bm = BlockchainManager(genesis.to_dict())
    block = Block('transaction', 'prev_block_hash')
    bm.set_new_block(block)
    assert len(bm.chain) == 2
    assert bm.chain[0] == genesis.to_dict()
    assert bm.chain[1] == block

def test__get_double_sha256():
    bm = BlockchainManager(None)
    actual_hash = hashlib.sha256(hashlib.sha256('abc'.encode('utf-8')).digest()).digest()
    assert bm._get_double_sha256('abc') == actual_hash

def test_get_hash():
    bm = BlockchainManager(None)
    block = Block('transaction', 'prev_block_hash')
    block_json = json.dumps(block.to_dict(), sort_keys=True)
    hash_b = hashlib.sha256(hashlib.sha256(block_json.encode('utf-8')).digest()).digest()
    actual_hash = binascii.hexlify(hash_b).decode('ascii')
    assert bm.get_hash(block.to_dict()) == actual_hash

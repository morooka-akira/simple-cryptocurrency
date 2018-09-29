from blockchain.block import Block
import json

def test_init():
    actual_transaction = 'transaction'
    actual_previous_block = 'previous_block'
    block = Block(actual_transaction, actual_previous_block)
    assert block.timestamp is not None
    assert block.transaction is actual_transaction
    assert block.previous_block is actual_previous_block

def test_to_dict():
    actual_transaction = 'transaction'
    actual_previous_block = 'previous_block'
    block = Block(actual_transaction, actual_previous_block)
    assert isinstance(block.to_dict(), dict) == True
    assert block.to_dict()['transaction'] == json.dumps(actual_transaction)
    assert block.to_dict()['previous_block'] == actual_previous_block

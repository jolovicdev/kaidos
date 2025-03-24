import os
import unittest
from datetime import datetime

from Kaidos.core.blockchain import Blockchain
from Kaidos.core.block import Block
from Kaidos.core.transaction_manager import TransactionManager
from Kaidos.core.exceptions import InvalidBlockError


class TestBlockchain(unittest.TestCase):
    
    def setUp(self):
        self.test_db = "test_blockchain.db"
        
        if os.path.exists(self.test_db):
            os.remove(self.test_db)
            
        self.blockchain = Blockchain(self.test_db)
        self.tx_manager = TransactionManager(self.test_db)
    
    def tearDown(self):
        self.blockchain.close()
        self.tx_manager.close()
        
        if os.path.exists(self.test_db):
            os.remove(self.test_db)
    
    def test_genesis_block(self):
        genesis = self.blockchain.get_block_by_index(0)
        
        self.assertEqual(genesis["index"], 0)
        self.assertEqual(genesis["previous_hash"], "0" * 64)
        self.assertEqual(len(genesis["transactions"]), 0)
        
        self.assertTrue(isinstance(genesis["hash"], str))
        self.assertEqual(len(genesis["hash"]), 64)
    
    def test_add_block(self):
        genesis = self.blockchain.get_latest_block()
        
        miner_address = "KD123456789TESTADDRESS"
        
        coinbase_tx = self.tx_manager.create_coinbase_transaction(
            miner_address, 
            self.blockchain.calculate_block_reward(1)
        )
        
        new_block = Block(
            index=1,
            transactions=[coinbase_tx],
            previous_hash=genesis["hash"],
            miner_address=miner_address
        )
        
        new_block.mine_block(4)  # Use fixed difficulty of 4 for tests
        
        block_id = self.blockchain.add_block(new_block)
        
        self.assertIsNotNone(block_id)
        
        block = self.blockchain.get_block_by_index(1)
        
        self.assertEqual(block["index"], 1)
        self.assertEqual(block["previous_hash"], genesis["hash"])
        self.assertEqual(len(block["transactions"]), 1)
        self.assertEqual(block["miner_address"], miner_address)
        
        self.assertTrue(block["transactions"][0].get("coinbase", False))
        self.assertEqual(block["transactions"][0]["outputs"][0]["address"], miner_address)
    
    def test_add_invalid_block(self):
        genesis = self.blockchain.get_latest_block()
        
        invalid_block = Block(
            index=2,  # Should be 1
            transactions=[],
            previous_hash=genesis["hash"]
        )
        
        invalid_block.mine_block(4)  # Use fixed difficulty of 4 for tests
        
        with self.assertRaises(InvalidBlockError):
            self.blockchain.add_block(invalid_block)
    
    def test_chain_validation(self):
        self.assertTrue(self.blockchain.is_chain_valid())
        
        miner_address = "KD123456789TESTADDRESS"
        
        coinbase_tx = self.tx_manager.create_coinbase_transaction(
            miner_address, 
            self.blockchain.calculate_block_reward(1)
        )
        
        genesis = self.blockchain.get_latest_block()
        new_block = Block(
            index=1,
            transactions=[coinbase_tx],
            previous_hash=genesis["hash"],
            miner_address=miner_address
        )
        new_block.mine_block(4)  # Use fixed difficulty of 4 for tests
        self.blockchain.add_block(new_block)
        
        self.assertTrue(self.blockchain.is_chain_valid())
    
    def test_get_blocks_range(self):
        miner_address = "KD123456789TESTADDRESS"
        
        for i in range(1, 5):
            latest = self.blockchain.get_latest_block()
            
            coinbase_tx = self.tx_manager.create_coinbase_transaction(
                miner_address, 
                self.blockchain.calculate_block_reward(i)
            )
            
            new_block = Block(
                index=i,
                transactions=[coinbase_tx],
                previous_hash=latest["hash"],
                miner_address=miner_address
            )
            new_block.mine_block(4)  # Use fixed difficulty of 4 for tests
            self.blockchain.add_block(new_block)
        
        blocks = self.blockchain.get_blocks_range(1, 3)
        
        self.assertEqual(len(blocks), 3)
        self.assertEqual(blocks[0]["index"], 1)
        self.assertEqual(blocks[1]["index"], 2)
        self.assertEqual(blocks[2]["index"], 3)
    
    def test_get_chain_length(self):
        self.assertEqual(self.blockchain.get_chain_length(), 1)
        
        miner_address = "KD123456789TESTADDRESS"
        
        coinbase_tx = self.tx_manager.create_coinbase_transaction(
            miner_address, 
            self.blockchain.calculate_block_reward(1)
        )
        
        genesis = self.blockchain.get_latest_block()
        new_block = Block(
            index=1,
            transactions=[coinbase_tx],
            previous_hash=genesis["hash"],
            miner_address=miner_address
        )
        new_block.mine_block(4)  # Use fixed difficulty of 4 for tests
        self.blockchain.add_block(new_block)
        
        self.assertEqual(self.blockchain.get_chain_length(), 2)
    
    def test_block_reward(self):
        self.assertEqual(self.blockchain.calculate_block_reward(1), 50.0)
        
        self.assertEqual(self.blockchain.calculate_block_reward(210000), 25.0)
        
        self.assertEqual(self.blockchain.calculate_block_reward(420000), 12.5)


if __name__ == "__main__":
    unittest.main()

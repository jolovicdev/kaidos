import os
import unittest
from datetime import datetime

from Kaidos.core.transaction_manager import TransactionManager
from Kaidos.wallet.wallet import Wallet
from Kaidos.core.exceptions import InvalidTransactionError, InsufficientFundsError


class TestTransactionManager(unittest.TestCase):
    
    def setUp(self):
        self.test_db = "test_transactions.db"
        self.test_wallet_db = "test_wallets.db"
        
        if os.path.exists(self.test_db):
            os.remove(self.test_db)
        if os.path.exists(self.test_wallet_db):
            os.remove(self.test_wallet_db)
            
        self.tx_manager = TransactionManager(self.test_db)
        self.wallet = Wallet(self.test_wallet_db)
        
        # Create a test wallet and address
        self.wallet_result = self.wallet.create_wallet()
        self.address = self.wallet_result['address']
        
        # Create a second wallet for testing transactions
        self.wallet2_result = self.wallet.create_wallet()
        self.address2 = self.wallet2_result['address']
    
    def tearDown(self):
        self.tx_manager.close()
        self.wallet.close()
        
        if os.path.exists(self.test_db):
            os.remove(self.test_db)
        if os.path.exists(self.test_wallet_db):
            os.remove(self.test_wallet_db)
    
    def test_add_utxo(self):
        txid = "test_txid"
        vout = 0
        amount = 50.0
        
        utxo_id = self.tx_manager.add_utxo(txid, vout, self.address, amount)
        
        self.assertIsNotNone(utxo_id)
        
        # Check that UTXO was stored
        utxos = self.tx_manager.get_utxos_for_address(self.address)
        
        self.assertEqual(len(utxos), 1)
        self.assertEqual(utxos[0]["txid"], txid)
        self.assertEqual(utxos[0]["vout"], vout)
        self.assertEqual(utxos[0]["address"], self.address)
        self.assertEqual(utxos[0]["amount"], amount)
    
    def test_get_balance(self):
        # Add some UTXOs
        self.tx_manager.add_utxo("txid1", 0, self.address, 50.0)
        self.tx_manager.add_utxo("txid2", 0, self.address, 30.0)
        
        balance = self.tx_manager.get_balance(self.address)
        
        self.assertEqual(balance, 80.0)
    
    def test_mark_utxo_spent(self):
        txid = "test_txid"
        vout = 0
        
        # Add a UTXO
        self.tx_manager.add_utxo(txid, vout, self.address, 50.0)
        
        # Mark it as spent
        self.tx_manager._mark_utxo_spent(txid, vout)
        
        # Check that it's marked as spent
        utxo = self.tx_manager._get_utxo(txid, vout)
        self.assertTrue(utxo.get("spent_in_mempool", False))
        
        # Check that it's considered spent in mempool
        self.assertTrue(self.tx_manager._is_utxo_spent_in_mempool(txid, vout))
    
    def test_remove_utxo(self):
        txid = "test_txid"
        vout = 0
        
        # Add a UTXO
        self.tx_manager.add_utxo(txid, vout, self.address, 50.0)
        
        # Remove it
        result = self.tx_manager.remove_utxo(txid, vout)
        
        self.assertTrue(result)
        
        # Check that it's gone
        utxos = self.tx_manager.get_utxos_for_address(self.address)
        self.assertEqual(len(utxos), 0)
    
    def test_create_coinbase_transaction(self):
        reward = 50.0
        fees = 1.5
        
        tx = self.tx_manager.create_coinbase_transaction(self.address, reward, fees)
        
        self.assertIn("txid", tx)
        self.assertEqual(len(tx["inputs"]), 0)
        self.assertEqual(len(tx["outputs"]), 1)
        self.assertEqual(tx["outputs"][0]["address"], self.address)
        self.assertEqual(tx["outputs"][0]["amount"], reward + fees)
        self.assertTrue(tx.get("coinbase", False))
    
    def test_calculate_transaction_fee(self):
        # Add some UTXOs
        self.tx_manager.add_utxo("txid1", 0, self.address, 50.0)
        
        # Create a transaction that spends less than the input
        tx = {
            "inputs": [{"txid": "txid1", "vout": 0}],
            "outputs": [{"address": self.address2, "amount": 40.0}]
        }
        
        fee = self.tx_manager.calculate_transaction_fee(tx)
        
        self.assertEqual(fee, 10.0)
    
    def test_process_block_transactions(self):
        # Add a UTXO
        self.tx_manager.add_utxo("txid1", 0, self.address, 50.0)
        
        # Create a block with transactions
        block = {
            "transactions": [
                {
                    "txid": "coinbase_tx",
                    "inputs": [],
                    "outputs": [{"address": self.address, "amount": 50.0}],
                    "coinbase": True
                },
                {
                    "txid": "tx1",
                    "inputs": [{"txid": "txid1", "vout": 0}],
                    "outputs": [
                        {"address": self.address2, "amount": 40.0},
                        {"address": self.address, "amount": 9.0}
                    ]
                }
            ]
        }
        
        # Process the block
        self.tx_manager.process_block_transactions(block)
        
        # Check that the original UTXO is gone
        utxo = self.tx_manager._get_utxo("txid1", 0)
        self.assertIsNone(utxo)
        
        # Check that new UTXOs were created
        utxos = self.tx_manager.get_utxos_for_address(self.address)
        self.assertEqual(len(utxos), 2)  # Coinbase output + change output
        
        utxos2 = self.tx_manager.get_utxos_for_address(self.address2)
        self.assertEqual(len(utxos2), 1)  # Payment output
        
        # Check balances
        self.assertEqual(self.tx_manager.get_balance(self.address), 59.0)  # 50 (coinbase) + 9 (change)
        self.assertEqual(self.tx_manager.get_balance(self.address2), 40.0)


if __name__ == "__main__":
    unittest.main()

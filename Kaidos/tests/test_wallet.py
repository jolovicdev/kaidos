import os
import unittest
from datetime import datetime

from Kaidos.wallet.wallet import Wallet
from Kaidos.core.exceptions import KeyGenerationError, SignatureError


class TestWallet(unittest.TestCase):
    
    def setUp(self):
        self.test_db = "test_wallets.db"
        
        if os.path.exists(self.test_db):
            os.remove(self.test_db)
            
        self.wallet = Wallet(self.test_db)
    
    def tearDown(self):
        self.wallet.close()
        
        if os.path.exists(self.test_db):
            os.remove(self.test_db)
    
    def test_create_wallet(self):
        result = self.wallet.create_wallet()
        
        self.assertIn('wallet_id', result)
        self.assertIn('address', result)
        self.assertIn('public_key', result)
        
        # Check that wallet was stored in database
        wallet = self.wallet.get_wallet(result['wallet_id'])
        self.assertIsNotNone(wallet)
        self.assertEqual(wallet['wallet_id'], result['wallet_id'])
        self.assertFalse(wallet.get('encrypted', False))
        
        # Check that address was created
        addresses = self.wallet.list_addresses(result['wallet_id'])
        self.assertEqual(len(addresses), 1)
        self.assertEqual(addresses[0]['address'], result['address'])
    
    def test_create_encrypted_wallet(self):
        passphrase = "test_passphrase"
        result = self.wallet.create_wallet(passphrase)
        
        wallet = self.wallet.get_wallet(result['wallet_id'])
        self.assertTrue(wallet.get('encrypted', False))
    
    def test_create_address(self):
        # Create a wallet first
        wallet_result = self.wallet.create_wallet()
        wallet_id = wallet_result['wallet_id']
        
        # Create a new address
        address_result = self.wallet.create_address(wallet_id)
        
        self.assertIn('address', address_result)
        self.assertIn('public_key', address_result)
        
        # Check that address was stored in database
        addresses = self.wallet.list_addresses(wallet_id)
        self.assertEqual(len(addresses), 2)  # Initial address + new address
        
        # Verify the new address is in the list
        address_found = False
        for addr in addresses:
            if addr['address'] == address_result['address']:
                address_found = True
                break
        
        self.assertTrue(address_found)
    
    def test_list_wallets(self):
        # Create a few wallets
        wallet1 = self.wallet.create_wallet()
        wallet2 = self.wallet.create_wallet()
        
        wallets = self.wallet.list_wallets()
        
        self.assertEqual(len(wallets), 2)
        
        # Check that both wallets are in the list
        wallet_ids = [w['wallet_id'] for w in wallets]
        self.assertIn(wallet1['wallet_id'], wallet_ids)
        self.assertIn(wallet2['wallet_id'], wallet_ids)
        
        # Check that addresses are included
        for w in wallets:
            self.assertIn('addresses', w)
            self.assertEqual(len(w['addresses']), 1)
    
    def test_list_addresses(self):
        # Create a wallet
        wallet_result = self.wallet.create_wallet()
        wallet_id = wallet_result['wallet_id']
        
        # Create additional addresses
        addr1 = self.wallet.create_address(wallet_id)
        addr2 = self.wallet.create_address(wallet_id)
        
        addresses = self.wallet.list_addresses(wallet_id)
        
        self.assertEqual(len(addresses), 3)  # Initial + 2 new addresses
        
        # Check that all addresses are in the list
        addr_list = [a['address'] for a in addresses]
        self.assertIn(wallet_result['address'], addr_list)
        self.assertIn(addr1['address'], addr_list)
        self.assertIn(addr2['address'], addr_list)
    
    def test_get_wallet_by_address(self):
        # Create a wallet
        wallet_result = self.wallet.create_wallet()
        wallet_id = wallet_result['wallet_id']
        address = wallet_result['address']
        
        # Get wallet by address
        wallet = self.wallet.get_wallet_by_address(address)
        
        self.assertIsNotNone(wallet)
        self.assertEqual(wallet['wallet_id'], wallet_id)
    
    def test_sign_transaction_input(self):
        # Create a wallet
        wallet_result = self.wallet.create_wallet()
        address = wallet_result['address']
        
        # Sign a transaction input
        txid = "test_txid"
        vout = 0
        
        signature = self.wallet.sign_transaction_input(txid, vout, address)
        
        self.assertIsNotNone(signature)
        self.assertTrue(isinstance(signature, str))
        
        # Verify the signature
        result = self.wallet.verify_input_signature(
            {"txid": txid, "vout": vout, "signature": signature},
            address
        )
        
        self.assertTrue(result)
    
    def test_encrypted_wallet_operations(self):
        passphrase = "test_passphrase"
        
        # Create an encrypted wallet
        wallet_result = self.wallet.create_wallet(passphrase)
        wallet_id = wallet_result['wallet_id']
        address = wallet_result['address']
        
        # Create a new address with passphrase
        addr_result = self.wallet.create_address(wallet_id, passphrase)
        
        # Sign a transaction input with passphrase
        txid = "test_txid"
        vout = 0
        
        signature = self.wallet.sign_transaction_input(txid, vout, address, passphrase)
        
        self.assertIsNotNone(signature)
        
        # Verify the signature
        result = self.wallet.verify_input_signature(
            {"txid": txid, "vout": vout, "signature": signature},
            address
        )
        
        self.assertTrue(result)
        
        # Test with wrong passphrase
        with self.assertRaises(SignatureError):
            self.wallet.sign_transaction_input(txid, vout, address, "wrong_passphrase")


if __name__ == "__main__":
    unittest.main()

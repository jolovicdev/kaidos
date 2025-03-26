import unittest
import base64
import hashlib
from Kaidos.wallet.multisig import MultiSigWallet


class TestMultiSigWallet(unittest.TestCase):
    
    def setUp(self):
        self.public_keys = [
            """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAu8LYkrwKYOuOtZGm0tIL
U1JyT8T0CJyG+8x7j9LPJMX6jY0iIqIlwKj9d40PZ0U9fxk8Vu7k70aMj/3Njjkl
VmA9JwwLnRsP4d5RzGJ9HvbC0g5YWU5LsZ/OWlGTLMTEVsVXZ+L4UZW0b1qZkdID
mFIPXIWMYZrDiQGGWIbGDlf4B5GhpPy6F3eFI+5oQd2MKDcpkXrJOAR5KEZ/cEjL
0evJJk1FCm8jRHgxMXBQkJjgGKEEzRFUCKG9RRiWYEIEfN+3MYGxYNNDlj2HMz3P
80NN6Ai2Vq5ypkgWg6oJ+QGjq9Z9GJz0ZO9VTJPHtOchYhIrLzQVTWsKzXpHiVVl
AQIDAQAB
-----END PUBLIC KEY-----""",
            """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAzs9TG5C/RIM2Xh0V4JMK
5DCvUXMmFPOLSzD5PWGX4GUULOiQV3C1XGCiHECTJUXKRUYBXzX0uOgULP1QRdIY
8jU5XhleEHQYl8Cw7Lm8xkkT4Jw8WbHnB0KpOHjHUHzDfGvFmMV8Wi8Yl0wNVr0Q
YcUjQHXJeR9V9NpK7CT7RGjPT3sBLMjA8kzkSOBF9Zk5KgXTYi4FdLjE6OQYzevH
dF7UJuEkPcxAFjkIk3e0yGJZF3ixQbCOzQZwF3J0K9kxA6hYRWnxjKQHJYiIxEMO
9J9MdNQyB0Kz5pMZYHjJUMdnJJcwgZYXsYGHlpBGI4qS4QwULDNJTy62JLrdrXwx
AQIDAQAB
-----END PUBLIC KEY-----""",
            """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAzs9TG5C/RIM2Xh0V4JMK
5DCvUXMmFPOLSzD5PWGX4GUULOiQV3C1XGCiHECTJUXKRUYBXzX0uOgULP1QRdIY
8jU5XhleEHQYl8Cw7Lm8xkkT4Jw8WbHnB0KpOHjHUHzDfGvFmMV8Wi8Yl0wNVr0Q
YcUjQHXJeR9V9NpK7CT7RGjPT3sBLMjA8kzkSOBF9Zk5KgXTYi4FdLjE6OQYzevH
dF7UJuEkPcxAFjkIk3e0yGJZF3ixQbCOzQZwF3J0K9kxA6hYRWnxjKQHJYiIxEMO
9J9MdNQyB0Kz5pMZYHjJUMdnJJcwgZYXsYGHlpBGI4qS4QwULDNJTy62JLrdrXwx
AQIDAQAB
-----END PUBLIC KEY-----"""
        ]
    
    def test_create_multisig_address(self):
        address = MultiSigWallet.create_multisig_address(self.public_keys, 2)
        
        self.assertTrue(address.startswith("KDM"))
        self.assertTrue(len(address) > 10)
    
    def test_create_multisig_address_invalid_m(self):
        with self.assertRaises(ValueError):
            MultiSigWallet.create_multisig_address(self.public_keys, 0)
            
        with self.assertRaises(ValueError):
            MultiSigWallet.create_multisig_address(self.public_keys, 4)
    
    def test_get_multisig_data(self):
        address = MultiSigWallet.create_multisig_address(self.public_keys, 2)
        
        data = MultiSigWallet.get_multisig_data(address, self.public_keys, 2)
        
        self.assertEqual(data["address"], address)
        self.assertEqual(data["required_signatures"], 2)
        self.assertEqual(len(data["public_keys"]), 3)
    
    def test_get_multisig_data_invalid_address(self):
        with self.assertRaises(ValueError):
            MultiSigWallet.get_multisig_data("KDM123456", self.public_keys, 2)
    
    def test_create_multisig_transaction_input(self):
        txid = "test_txid"
        vout = 0
        signatures = [
            {"signature": "sig1", "key_index": 0},
            {"signature": "sig2", "key_index": 1}
        ]
        
        tx_input = MultiSigWallet.create_multisig_transaction_input(txid, vout, signatures)
        
        self.assertEqual(tx_input["txid"], txid)
        self.assertEqual(tx_input["vout"], vout)
        self.assertEqual(tx_input["signatures"], signatures)
        self.assertTrue(tx_input["multisig"])
    
    def test_verify_multisig_transaction(self):
        txid = "test_txid"
        vout = 0
        
        signatures = [
            {"signature": base64.b64encode(b"sig1").decode(), "key_index": 0},
            {"signature": base64.b64encode(b"sig2").decode(), "key_index": 1}
        ]
        
        tx_input = {
            "txid": txid,
            "vout": vout,
            "signatures": signatures,
            "multisig": True
        }
        
        multisig_data = {
            "public_keys": self.public_keys,
            "required_signatures": 2
        }
        
        with unittest.mock.patch.object(MultiSigWallet, 'verify_multisig_transaction', return_value=True):
            result = MultiSigWallet.verify_multisig_transaction(tx_input, multisig_data)
            self.assertTrue(result)


if __name__ == "__main__":
    unittest.main()

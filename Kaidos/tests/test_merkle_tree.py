import unittest
from Kaidos.core.merkle_tree import MerkleTree


class TestMerkleTree(unittest.TestCase):
    
    def test_create_merkle_root_empty(self):
        root = MerkleTree.create_merkle_root([])
        self.assertEqual(root, "0" * 64)
    
    def test_create_merkle_root_single(self):
        tx = {"txid": "abc123"}
        root = MerkleTree.create_merkle_root([tx])
        self.assertIsNotNone(root)
        self.assertEqual(len(root), 64)
    
    def test_create_merkle_root_multiple(self):
        transactions = [
            {"txid": "tx1"},
            {"txid": "tx2"},
            {"txid": "tx3"},
            {"txid": "tx4"}
        ]
        root = MerkleTree.create_merkle_root(transactions)
        self.assertIsNotNone(root)
        self.assertEqual(len(root), 64)
    
    def test_create_merkle_root_odd_count(self):
        transactions = [
            {"txid": "tx1"},
            {"txid": "tx2"},
            {"txid": "tx3"}
        ]
        root = MerkleTree.create_merkle_root(transactions)
        self.assertIsNotNone(root)
        self.assertEqual(len(root), 64)
    
    def test_generate_and_verify_proof(self):
        transactions = [
            {"txid": "tx1"},
            {"txid": "tx2"},
            {"txid": "tx3"},
            {"txid": "tx4"}
        ]
        
        root = MerkleTree.create_merkle_root(transactions)
        tx_hash = "tx2"
        proof = MerkleTree.generate_proof(tx_hash, transactions)
        
        self.assertIsNotNone(proof)
        self.assertTrue(MerkleTree.verify_transaction(tx_hash, root, proof))
    
    def test_verify_invalid_proof(self):
        transactions = [
            {"txid": "tx1"},
            {"txid": "tx2"},
            {"txid": "tx3"},
            {"txid": "tx4"}
        ]
        
        root = MerkleTree.create_merkle_root(transactions)
        tx_hash = "tx2"
        proof = MerkleTree.generate_proof(tx_hash, transactions)
        
        if proof:
            proof[0]["hash"] = "invalid_hash"
        
        self.assertFalse(MerkleTree.verify_transaction(tx_hash, root, proof))
    
    def test_generate_proof_nonexistent_tx(self):
        transactions = [
            {"txid": "tx1"},
            {"txid": "tx2"}
        ]
        
        proof = MerkleTree.generate_proof("nonexistent", transactions)
        self.assertIsNone(proof)


if __name__ == "__main__":
    unittest.main()

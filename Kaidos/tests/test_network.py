import os
import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime

import requests

from Kaidos.network.node import Node
from Kaidos.core.blockchain import Blockchain
from Kaidos.core.transaction_manager import TransactionManager


class TestNetwork(unittest.TestCase):
    
    def setUp(self):
        self.test_db = "test_node.db"
        
        if os.path.exists(self.test_db):
            os.remove(self.test_db)
            
        # Mock Flask app to avoid actually starting a server
        with patch('flask.Flask.run'):
            self.node = Node(host="localhost", port=5000, db_path=self.test_db)
    
    def tearDown(self):
        self.node.close()
        
        if os.path.exists(self.test_db):
            os.remove(self.test_db)
    
    @patch('requests.post')
    def test_connect_to_peer(self, mock_post):
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        # Mock sync and discovery methods
        self.node._sync_with_peer = MagicMock()
        self.node._discover_peers_from_peer = MagicMock()
        
        # Connect to peer
        result = self.node._connect_to_peer("localhost:5001")
        
        # Check that connection was successful
        self.assertTrue(result)
        
        # Check that peer was added to database with normalized address
        peer = self.node.peers.find_one({"address": "127.0.0.1:5001"})
        self.assertIsNotNone(peer)
        self.assertIn("last_seen", peer)
        
        # Check that sync and discovery methods were called
        self.node._sync_with_peer.assert_called_once_with("localhost:5001")
        self.node._discover_peers_from_peer.assert_called_once_with("localhost:5001")
    
    @patch('requests.post')
    def test_connect_to_peer_failure(self, mock_post):
        # Mock failed response
        mock_post.side_effect = requests.RequestException("Connection failed")
        
        # Connect to peer
        result = self.node._connect_to_peer("localhost:5001")
        
        # Check that connection failed
        self.assertFalse(result)
    
    @patch('requests.get')
    def test_sync_with_peer(self, mock_get):
        # Mock successful response with a longer chain
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "index": 5,
            "hash": "test_hash"
        }
        mock_get.return_value = mock_response
        
        # Mock run_consensus_with_peer
        self.node._run_consensus_with_peer = MagicMock()
        
        # Sync with peer
        self.node._sync_with_peer("localhost:5001")
        
        # Check that consensus was run
        self.node._run_consensus_with_peer.assert_called_once_with("localhost:5001")
    
    @patch('requests.get')
    def test_sync_with_peer_shorter_chain(self, mock_get):
        # Add a block to our chain
        miner_address = "KD123456789TESTADDRESS"
        latest = self.node.blockchain.get_latest_block()
        coinbase_tx = self.node.tx_manager.create_coinbase_transaction(
            miner_address, 
            self.node.blockchain.calculate_block_reward(1)
        )
        from Kaidos.core.block import Block
        new_block = Block(
            index=1,
            transactions=[coinbase_tx],
            previous_hash=latest["hash"],
            miner_address=miner_address
        )
        new_block.mine_block(4)  # Use fixed difficulty of 4 for tests
        self.node.blockchain.add_block(new_block)
        
        # Mock successful response with a shorter chain
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "index": 0,
            "hash": "genesis_hash"
        }
        mock_get.return_value = mock_response
        
        # Mock run_consensus_with_peer
        self.node._run_consensus_with_peer = MagicMock()
        
        # Sync with peer
        self.node._sync_with_peer("localhost:5001")
        
        # Check that consensus was not run
        self.node._run_consensus_with_peer.assert_not_called()
    
    @patch('requests.get')
    def test_discover_peers_from_peer(self, mock_get):
        # Mock successful response with peers
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "peers": [
                {"address": "localhost:5001"},
                {"address": "localhost:5002"},
                {"address": "localhost:5000"}  # Our own address
            ]
        }
        mock_get.return_value = mock_response
        
        # Discover peers
        self.node._discover_peers_from_peer("localhost:5001")
        
        # Check that peers were added to database
        peers = list(self.node.peers.find({}))
        self.assertEqual(len(peers), 2)  # Should not include our own address
        
        # Check normalized peer addresses
        addresses = [p["address"] for p in peers]
        self.assertIn("127.0.0.1:5001", addresses)
        self.assertIn("127.0.0.1:5002", addresses)
        
        # Check source field
        peer = self.node.peers.find_one({"address": "127.0.0.1:5002"})
        self.assertEqual(peer["source"], "localhost:5001")
    
    @patch('requests.get')
    def test_run_consensus_with_peer(self, mock_get):
        # Mock successful response with a chain
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "blocks": [
                {"index": 0, "hash": "genesis_hash"},
                {"index": 1, "hash": "block1_hash"}
            ]
        }
        mock_get.return_value = mock_response
        
        # Mock resolve_conflicts
        self.node.blockchain.resolve_conflicts = MagicMock(return_value=True)
        
        # Run consensus
        self.node._run_consensus_with_peer("localhost:5001")
        
        # Check that resolve_conflicts was called with the peer's chain
        self.node.blockchain.resolve_conflicts.assert_called_once()
        args = self.node.blockchain.resolve_conflicts.call_args[0][0]
        self.assertEqual(len(args), 1)
        self.assertEqual(len(args[0]), 2)
    
    @patch('requests.post')
    def test_broadcast_block(self, mock_post):
        # Add some peers
        self.node.peers.insert({"address": "127.0.0.1:5001"})
        self.node.peers.insert({"address": "127.0.0.1:5002"})
        
        # Create a block to broadcast
        block = {
            "index": 1,
            "hash": "test_hash",
            "previous_hash": "genesis_hash",
            "transactions": []
        }
        
        # Broadcast block
        self.node._broadcast_block(block)
        
        # Check that post was called for each peer
        self.assertEqual(mock_post.call_count, 2)
        
        # Check that the block was sent
        for call in mock_post.call_args_list:
            self.assertEqual(call[1]["json"], block)
    
    @patch('requests.post')
    def test_broadcast_transaction(self, mock_post):
        # Add some peers
        self.node.peers.insert({"address": "127.0.0.1:5001"})
        self.node.peers.insert({"address": "127.0.0.1:5002"})
        
        # Create a transaction to broadcast
        transaction = {
            "txid": "test_txid",
            "inputs": [],
            "outputs": []
        }
        
        # Broadcast transaction
        self.node._broadcast_transaction(transaction)
        
        # Check that post was called for each peer
        self.assertEqual(mock_post.call_count, 2)
        
        # Check that the transaction was sent
        for call in mock_post.call_args_list:
            self.assertEqual(call[1]["json"], transaction)
    
    @patch('requests.get')
    def test_get_chains_from_peers(self, mock_get):
        # Add some peers
        self.node.peers.insert({"address": "127.0.0.1:5001"})
        self.node.peers.insert({"address": "127.0.0.1:5002"})
        
        # Mock successful responses
        mock_response1 = MagicMock()
        mock_response1.status_code = 200
        mock_response1.json.return_value = {
            "blocks": [
                {"index": 0, "hash": "genesis_hash"},
                {"index": 1, "hash": "block1_hash_1"}
            ]
        }
        
        mock_response2 = MagicMock()
        mock_response2.status_code = 200
        mock_response2.json.return_value = {
            "blocks": [
                {"index": 0, "hash": "genesis_hash"},
                {"index": 1, "hash": "block1_hash_2"}
            ]
        }
        
        mock_get.side_effect = [mock_response1, mock_response2]
        
        # Get chains
        chains = self.node._get_chains_from_peers()
        
        # Check that we got chains from both peers
        self.assertEqual(len(chains), 2)
        self.assertEqual(len(chains[0]), 2)
        self.assertEqual(len(chains[1]), 2)
        
        # Check that the chains are different
        self.assertNotEqual(chains[0][1]["hash"], chains[1][1]["hash"])


if __name__ == "__main__":
    unittest.main()

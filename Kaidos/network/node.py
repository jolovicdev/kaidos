import json
import requests
from datetime import datetime
from typing import List, Dict, Any, Optional, Set
from flask import Flask, request, jsonify
from zenithdb import Database

from Kaidos.core.blockchain import Blockchain
from Kaidos.core.transaction_manager import TransactionManager
from Kaidos.core.block import Block
from Kaidos.core.exceptions import InvalidBlockError, InvalidTransactionError


class Node:
    
    def __init__(
        self, 
        host: str = "0.0.0.0", 
        port: int = 5000, 
        db_path: str = "kaidos_node.db"
    ):
        self.host = host
        self.port = port
        self.db = Database(db_path)
        self.peers = self.db.collection("peers")
        self._setup_indexes()
        
        # Initialize blockchain and transaction manager
        self.blockchain = Blockchain(db_path)
        self.tx_manager = TransactionManager(db_path)
        
        # Initialize Flask app
        self.app = Flask(__name__)
        self._setup_routes()
    
    def _setup_indexes(self) -> None:
        self.db.create_index("peers", "address", unique=True)
    
    def _normalize_peer_address(self, address: str) -> str:
        # Split into host and port
        if ':' not in address:
            return address
            
        host, port = address.split(':')
        
        # Convert localhost and 0.0.0.0 to 127.0.0.1 for consistency
        if host in ('localhost', '0.0.0.0'):
            host = '127.0.0.1'
            
        return f"{host}:{port}"
    
    def _setup_routes(self) -> None:
        
        @self.app.route('/blocks', methods=['GET', 'POST'])
        def blocks():
            if request.method == 'GET':
                start = request.args.get('start', 0, type=int)
                end = request.args.get('end', None, type=int)
                
                if end is None:
                    end = self.blockchain.get_chain_length() - 1
                    
                blocks = self.blockchain.get_blocks_range(start, end)
                return jsonify({
                    'blocks': blocks,
                    'length': len(blocks)
                })
            elif request.method == 'POST':
                # Handle adding a block sent from another node
                data = request.get_json()
                if not data:
                    return jsonify({'error': 'No block data provided'}), 400
                
                try:
                    # Create a Block object from the data
                    from Kaidos.core.block import Block
                    if '_id' in data:
                        data.pop('_id')
                    
                    block = Block(**data)
                    
                    # Add the block to the chain
                    self.blockchain.add_block(block)
                    
                    return jsonify({'message': 'Block added successfully'})
                    
                except Exception as e:
                    return jsonify({'error': str(e)}), 400
        
        @self.app.route('/blocks/latest', methods=['GET'])
        def get_latest_block():
            block = self.blockchain.get_latest_block()
            return jsonify(block)
        
        @self.app.route('/blocks/<block_hash>', methods=['GET'])
        def get_block(block_hash):
            block = self.blockchain.get_block_by_hash(block_hash)
            if block:
                return jsonify(block)
            return jsonify({'error': 'Block not found'}), 404
        
        @self.app.route('/blocks/mine', methods=['POST'])
        def mine_block():
            data = request.get_json() or {}
            miner_address = data.get('miner_address')
            
            if not miner_address:
                return jsonify({'error': 'Miner address is required'}), 400
                
            # Get pending transactions
            pending_tx = self.tx_manager.get_pending_transactions()
            
            # Get latest block
            latest_block = self.blockchain.get_latest_block()
            
            # Calculate block reward
            block_reward = self.blockchain.calculate_block_reward(latest_block['index'] + 1)
            
            # Calculate transaction fees (if there are pending transactions)
            total_fees = 0
            if pending_tx:
                total_fees = sum(self.tx_manager.calculate_transaction_fee(tx) for tx in pending_tx)
            
            # Create coinbase transaction
            coinbase_tx = self.tx_manager.create_coinbase_transaction(
                miner_address, 
                block_reward, 
                total_fees
            )
            
            # Add coinbase transaction to the beginning of the block
            # If there are no pending transactions, just use the coinbase transaction
            all_transactions = [coinbase_tx]
            if pending_tx:
                all_transactions.extend(pending_tx)
            
            # Create new block
            new_block = Block(
                index=latest_block['index'] + 1,
                transactions=all_transactions,
                previous_hash=latest_block['hash'],
                miner_address=miner_address
            )
            
            # Mine the block
            difficulty = self.blockchain.get_difficulty()
            new_block.mine_block(difficulty)
            
            try:
                # Add block to blockchain
                block_id = self.blockchain.add_block(new_block)
                
                # Broadcast new block to peers
                self._broadcast_block(new_block.to_dict())
                
                return jsonify({
                    'message': 'Block mined successfully',
                    'block': new_block.to_dict(),
                    'reward': block_reward + total_fees
                })
                
            except InvalidBlockError as e:
                return jsonify({'error': str(e)}), 400
        
        @self.app.route('/transactions', methods=['GET'])
        def get_transactions():
            transactions = self.tx_manager.get_pending_transactions()
            return jsonify({
                'transactions': transactions,
                'count': len(transactions)
            })
        
        @self.app.route('/transactions', methods=['POST'])
        def add_transaction():
            data = request.get_json()
            
            if not data:
                return jsonify({'error': 'No transaction data provided'}), 400
                
            try:
                # For UTXO model
                if 'inputs' in data and 'outputs' in data:
                    tx_id = self.tx_manager.add_transaction(
                        data['inputs'],
                        data['outputs'],
                        data.get('signature', '')
                    )
                else:
                    return jsonify({'error': 'Invalid transaction format'}), 400
                
                # Broadcast transaction to peers
                self._broadcast_transaction(data)
                
                return jsonify({
                    'message': 'Transaction added successfully',
                    'transaction_id': tx_id
                })
                
            except InvalidTransactionError as e:
                return jsonify({'error': str(e)}), 400
            except Exception as e:
                return jsonify({'error': f"Unexpected error: {str(e)}"}), 500
        
        @self.app.route('/transactions/<txid>', methods=['GET'])
        def get_transaction(txid):
            transaction = self.tx_manager.get_transaction(txid)
            if transaction:
                return jsonify(transaction)
            return jsonify({'error': 'Transaction not found'}), 404
        
        @self.app.route('/utxos/<address>', methods=['GET'])
        def get_utxos(address):
            utxos = self.tx_manager.get_utxos_for_address(address)
            return jsonify({
                'utxos': utxos,
                'count': len(utxos),
                'balance': self.tx_manager.get_balance(address)
            })
        
        @self.app.route('/peers', methods=['GET'])
        def get_peers():
            peers = list(self.peers.find({}))
            return jsonify({
                'peers': peers,
                'count': len(peers)
            })
        
        @self.app.route('/peers', methods=['POST'])
        def add_peer():
            data = request.get_json()
            
            if 'address' not in data:
                return jsonify({'error': 'Missing peer address'}), 400
            
            # Normalize the peer address to prevent duplicates
            normalized_address = self._normalize_peer_address(data['address'])
                
            # Check if peer already exists
            existing = self.peers.find_one({'address': normalized_address})
            if existing:
                return jsonify({'message': 'Peer already exists'}), 200
                
            # Add peer to database
            self.peers.insert({
                'address': normalized_address,
                'last_seen': datetime.now().isoformat()
            })
            
            # Connect to peer
            self._connect_to_peer(normalized_address)
            
            return jsonify({'message': 'Peer added successfully'})
        
        @self.app.route('/consensus', methods=['GET'])
        def consensus():
            chains = self._get_chains_from_peers()
            replaced = self.blockchain.resolve_conflicts(chains)
            
            if replaced:
                return jsonify({
                    'message': 'Chain was replaced',
                    'new_length': self.blockchain.get_chain_length()
                })
            else:
                return jsonify({
                    'message': 'Chain is authoritative',
                    'length': self.blockchain.get_chain_length()
                })
        
        @self.app.route('/debug/transaction', methods=['POST'])
        def debug_transaction():
            data = request.get_json()
            
            if not data:
                return jsonify({'error': 'No transaction data provided'}), 400
                
            try:
                # Validate without adding to mempool
                validation_result = self.tx_manager.debug_transaction(data)
                return jsonify({
                    'message': 'Transaction debug information',
                    'validation_result': validation_result
                })
            except Exception as e:
                return jsonify({'error': str(e)}), 400
    
    def start(self) -> None:
        self.app.run(host=self.host, port=self.port)
    
    def _connect_to_peer(self, address: str) -> bool:
        try:
            # Use normalized address for our own address
            our_address = self._normalize_peer_address(f'{self.host}:{self.port}')
            
            # Don't try to connect to ourselves
            if self._normalize_peer_address(address) == our_address:
                return False
                
            # Register ourselves with the peer
            response = requests.post(
                f'http://{address}/peers',
                json={'address': our_address}
            )
            
            if response.status_code == 200:
                normalized_address = self._normalize_peer_address(address)
                
                # Check if peer already exists
                existing = self.peers.find_one({'address': normalized_address})
                if not existing:
                    # Add peer to database
                    self.peers.insert({
                        'address': normalized_address,
                        'last_seen': datetime.now().isoformat()
                    })
                else:
                    # Update peer last seen
                    self.peers.update(
                        {'address': normalized_address},
                        {'$set': {'last_seen': datetime.now().isoformat()}}
                    )
                
                # Synchronize blockchain
                self._sync_with_peer(address)
                
                # Get additional peers from this peer
                self._discover_peers_from_peer(address)
                
                return True
                
            return False
            
        except requests.RequestException:
            return False
    
    def _sync_with_peer(self, address: str) -> None:
        try:
            # Get peer's latest block
            response = requests.get(f'http://{address}/blocks/latest')
            
            if response.status_code == 200:
                peer_latest_block = response.json()
                our_latest_block = self.blockchain.get_latest_block()
                
                # If peer has longer chain, run consensus
                if peer_latest_block["index"] > our_latest_block["index"]:
                    self._run_consensus_with_peer(address)
                    
        except requests.RequestException:
            pass
    
    def _discover_peers_from_peer(self, address: str) -> None:
        try:
            response = requests.get(f'http://{address}/peers')
            
            if response.status_code == 200:
                peer_data = response.json()
                our_address = self._normalize_peer_address(f'{self.host}:{self.port}')
                
                for peer in peer_data.get("peers", []):
                    peer_address = peer.get("address")
                    if not peer_address:
                        continue
                    
                    normalized_peer = self._normalize_peer_address(peer_address)
                    
                    # Don't add ourselves
                    if normalized_peer == our_address:
                        continue
                        
                    # Check if peer already exists
                    existing = self.peers.find_one({'address': normalized_peer})
                    if not existing:
                        # Add new peer
                        self.peers.insert({
                            'address': normalized_peer,
                            'last_seen': None,
                            'source': address
                        })
                        
        except requests.RequestException:
            pass
    
    def _run_consensus_with_peer(self, address: str) -> None:
        try:
            # Get peer's blockchain
            response = requests.get(f'http://{address}/blocks')
            
            if response.status_code == 200:
                peer_chain = response.json().get("blocks", [])
                
                # Run consensus with just this peer's chain
                self.blockchain.resolve_conflicts([peer_chain])
                
        except requests.RequestException:
            pass
    
    def _broadcast_block(self, block: Dict[str, Any]) -> None:
        peers = list(self.peers.find({}))
        
        for peer in peers:
            try:
                requests.post(
                    f'http://{peer["address"]}/blocks',
                    json=block
                )
            except requests.RequestException:
                continue
    
    def _broadcast_transaction(self, transaction: Dict[str, Any]) -> None:
        peers = list(self.peers.find({}))
        
        for peer in peers:
            try:
                requests.post(
                    f'http://{peer["address"]}/transactions',
                    json=transaction
                )
            except requests.RequestException:
                continue
    
    def _get_chains_from_peers(self) -> List[List[Dict[str, Any]]]:
        chains = []
        peers = list(self.peers.find({}))
        
        for peer in peers:
            try:
                response = requests.get(f'http://{peer["address"]}/blocks')
                
                if response.status_code == 200:
                    chain_data = response.json()
                    chains.append(chain_data['blocks'])
                    
            except requests.RequestException:
                continue
                
        return chains
    
    def close(self) -> None:
        self.db.close()
        self.blockchain.close()
        self.tx_manager.close()

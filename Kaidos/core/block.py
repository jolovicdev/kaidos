import hashlib
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

from Kaidos.core.merkle_tree import MerkleTree


class Block:
    
    def __init__(
        self, 
        index: int, 
        transactions: List[Dict[str, Any]], 
        previous_hash: str,
        timestamp: Optional[str] = None,
        nonce: int = 0,
        hash: Optional[str] = None,
        miner_address: Optional[str] = None,
        merkle_root: Optional[str] = None
    ):
        self.index = index
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.timestamp = timestamp or datetime.now().isoformat()
        self.nonce = nonce
        self.miner_address = miner_address
        self.merkle_root = merkle_root or MerkleTree.create_merkle_root(transactions)
        self.hash = hash or self.compute_hash()
    
    def compute_hash(self) -> str:
        block_data = {
            "index": self.index,
            "merkle_root": self.merkle_root,
            "previous_hash": self.previous_hash,
            "timestamp": self.timestamp,
            "nonce": self.nonce,
            "miner_address": self.miner_address
        }
        
        block_string = json.dumps(block_data, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()
    
    def mine_block(self, difficulty: int) -> None:
        target = '0' * difficulty
        
        while not self.hash.startswith(target):
            self.nonce += 1
            self.hash = self.compute_hash()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "index": self.index,
            "transactions": self.transactions,
            "previous_hash": self.previous_hash,
            "timestamp": self.timestamp,
            "nonce": self.nonce,
            "hash": self.hash,
            "miner_address": self.miner_address,
            "merkle_root": self.merkle_root
        }
    
    @classmethod
    def from_dict(cls, block_data: Dict[str, Any]) -> 'Block':
        return cls(
            index=block_data["index"],
            transactions=block_data["transactions"],
            previous_hash=block_data["previous_hash"],
            timestamp=block_data["timestamp"],
            nonce=block_data["nonce"],
            hash=block_data["hash"],
            miner_address=block_data.get("miner_address"),
            merkle_root=block_data.get("merkle_root")
        )
    
    def verify_transaction(self, tx_hash: str, proof: List[dict]) -> bool:
        """Verify that a transaction is included in this block using a Merkle proof."""
        return MerkleTree.verify_transaction(tx_hash, self.merkle_root, proof)
    
    def generate_transaction_proof(self, tx_hash: str) -> Optional[List[dict]]:
        """Generate a Merkle proof for a transaction in this block."""
        return MerkleTree.generate_proof(tx_hash, self.transactions)
    
    def __str__(self) -> str:
        return (
            f"Block {self.index} [Hash: {self.hash[:8]}...] "
            f"with {len(self.transactions)} transactions"
        )

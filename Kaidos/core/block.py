import hashlib
import json
from datetime import datetime
from typing import List, Dict, Any, Optional


class Block:
    
    def __init__(
        self, 
        index: int, 
        transactions: List[Dict[str, Any]], 
        previous_hash: str,
        timestamp: Optional[str] = None,
        nonce: int = 0,
        hash: Optional[str] = None,
        miner_address: Optional[str] = None
    ):
        self.index = index
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.timestamp = timestamp or datetime.now().isoformat()
        self.nonce = nonce
        self.miner_address = miner_address
        self.hash = hash or self.compute_hash()
    
    def compute_hash(self) -> str:
        block_data = {
            "index": self.index,
            "transactions": self.transactions,
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
            "miner_address": self.miner_address
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
            miner_address=block_data.get("miner_address")
        )
    
    def __str__(self) -> str:
        return (
            f"Block {self.index} [Hash: {self.hash[:8]}...] "
            f"with {len(self.transactions)} transactions"
        )

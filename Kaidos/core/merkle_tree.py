import hashlib
from typing import List, Optional


class MerkleTree:
    """Merkle Tree implementation for transaction verification."""
    
    @staticmethod
    def create_merkle_root(transactions: List[dict]) -> str:
        """Create a Merkle root hash from a list of transactions."""
        if not transactions:
            # Empty tree has a root of all zeros
            return "0" * 64
            
        # Create leaf nodes by hashing each transaction
        leaves = []
        for tx in transactions:
            # Convert transaction to string and hash it
            tx_string = str(tx.get("txid", ""))
            tx_hash = hashlib.sha256(tx_string.encode()).hexdigest()
            leaves.append(tx_hash)
            
        # Build the tree bottom-up
        return MerkleTree._build_merkle_tree(leaves)
    
    @staticmethod
    def _build_merkle_tree(hashes: List[str]) -> str:
        """Recursively build a Merkle tree from a list of hashes."""
        # Base case: single hash becomes the root
        if len(hashes) == 1:
            return hashes[0]
            
        # Create a new level of the tree
        new_level = []
        
        # Process pairs of hashes
        for i in range(0, len(hashes), 2):
            # If we have an odd number of hashes, duplicate the last one
            if i + 1 == len(hashes):
                combined = hashes[i] + hashes[i]
            else:
                combined = hashes[i] + hashes[i + 1]
                
            # Hash the combined string
            new_hash = hashlib.sha256(combined.encode()).hexdigest()
            new_level.append(new_hash)
            
        # Recursively build the next level
        return MerkleTree._build_merkle_tree(new_level)
    
    @staticmethod
    def verify_transaction(tx_hash: str, merkle_root: str, proof: List[dict]) -> bool:
        """Verify that a transaction is included in the Merkle tree."""
        if proof is None:
            return False
            
        # Hash the transaction ID
        current_hash = hashlib.sha256(tx_hash.encode()).hexdigest()
        
        for step in proof:
            sibling_hash = step["hash"]
            position = step["position"]
            
            if position == "left":
                combined = sibling_hash + current_hash
            else:
                combined = current_hash + sibling_hash
                
            current_hash = hashlib.sha256(combined.encode()).hexdigest()
            
        return current_hash == merkle_root
    
    @staticmethod
    def generate_proof(tx_hash: str, transactions: List[dict]) -> Optional[List[dict]]:
        """Generate a Merkle proof for a transaction."""
        # Convert transactions to hashes
        hashes = []
        tx_index = -1
        
        for i, tx in enumerate(transactions):
            tx_string = str(tx.get("txid", ""))
            current_hash = hashlib.sha256(tx_string.encode()).hexdigest()
            hashes.append(current_hash)
            
            # Check if this is the transaction we're looking for
            if tx.get("txid", "") == tx_hash:
                tx_index = i
                
        if tx_index == -1:
            return None
            
        return MerkleTree._generate_proof_recursive(hashes, tx_index)
    
    @staticmethod
    def _generate_proof_recursive(hashes: List[str], tx_index: int, proof: List[dict] = None) -> List[dict]:
        """Recursively generate a Merkle proof."""
        if proof is None:
            proof = []
            
        # Base case: single hash
        if len(hashes) == 1:
            return proof
            
        # Create a new level of the tree
        new_level = []
        new_tx_index = -1
        
        # Process pairs of hashes
        for i in range(0, len(hashes), 2):
            # If we have an odd number of hashes, duplicate the last one
            if i + 1 == len(hashes):
                left = hashes[i]
                right = hashes[i]
                combined = left + right
            else:
                left = hashes[i]
                right = hashes[i + 1]
                combined = left + right
                
            # Hash the combined string
            new_hash = hashlib.sha256(combined.encode()).hexdigest()
            new_level.append(new_hash)
            
            # If this pair includes our transaction, add to the proof
            if i == tx_index or i + 1 == tx_index:
                if i == tx_index:
                    proof.append({"hash": right, "position": "right"})
                else:
                    proof.append({"hash": left, "position": "left"})
                    
                new_tx_index = i // 2
                
        # Recursively build the next level
        return MerkleTree._generate_proof_recursive(new_level, new_tx_index, proof)

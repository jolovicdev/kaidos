from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple, Set
import json
from zenithdb import Database, Query

from Kaidos.core.exceptions import InvalidTransactionError, InsufficientFundsError


class TransactionManager:
    
    def __init__(self, db_path: str = "kaidos_chain.db"):
        self.db = Database(db_path)
        self.mempool = self.db.collection("mempool")
        self.utxos = self.db.collection("utxos")
        self._setup_indexes()
        
        self.mempool.set_validator(self._validate_transaction_document)
    
    def _setup_indexes(self) -> None:
        self.db.create_index("mempool", ["inputs.txid", "inputs.vout"])
        self.db.create_index("mempool", "timestamp")
        self.db.create_index("utxos", ["txid", "vout"], unique=True)
        self.db.create_index("utxos", "address")
    
    def _validate_transaction_document(self, tx: Dict[str, Any]) -> bool:
        if not all(field in tx for field in ["txid", "inputs", "outputs", "signature", "timestamp"]):
            return False
            
        if not isinstance(tx["inputs"], list) or not tx["inputs"]:
            return False
        for input_data in tx["inputs"]:
            if not all(field in input_data for field in ["txid", "vout", "signature"]):
                return False
                
        if not isinstance(tx["outputs"], list) or not tx["outputs"]:
            return False
        for output in tx["outputs"]:
            if not all(field in output for field in ["address", "amount"]):
                return False
            if not isinstance(output["amount"], (int, float)) or output["amount"] <= 0:
                return False
                
        return True
    
    def add_transaction(
        self, 
        inputs: List[Dict[str, Any]],
        outputs: List[Dict[str, Any]],
        signature: str
    ) -> str:
        tx_data = {
            "txid": self._generate_txid(inputs, outputs),
            "inputs": inputs,
            "outputs": outputs,
            "signature": signature,
            "timestamp": datetime.now().isoformat(),
            "status": "pending"
        }
        
        self.validate_transaction(tx_data)  # This will now raise an exception with details if it fails
        
        for tx_input in inputs:
            self._mark_utxo_spent(tx_input["txid"], tx_input["vout"])
        
        return self.mempool.insert(tx_data)
    
    def _generate_txid(self, inputs: List[Dict[str, Any]], outputs: List[Dict[str, Any]]) -> str:
        import hashlib
        
        tx_data = {
            "inputs": inputs,
            "outputs": outputs,
            "timestamp": datetime.now().isoformat()
        }
        
        tx_string = json.dumps(tx_data, sort_keys=True)
        return hashlib.sha256(tx_string.encode()).hexdigest()
    
    def validate_transaction(self, tx: Dict[str, Any]) -> bool:
        input_sum = 0
        
        if not tx.get("inputs") or not tx.get("outputs"):
            raise InvalidTransactionError("Transaction must have inputs and outputs")
            
        for tx_input in tx["inputs"]:
            if not all(field in tx_input for field in ["txid", "vout", "signature"]):
                raise InvalidTransactionError(f"Invalid input format: {tx_input}")
                
            utxo = self._get_utxo(tx_input["txid"], tx_input["vout"])
            if not utxo:
                raise InvalidTransactionError(f"UTXO not found: {tx_input['txid']}:{tx_input['vout']}")
            
            if self._is_utxo_spent_in_mempool(tx_input["txid"], tx_input["vout"]):
                raise InvalidTransactionError(f"UTXO already spent: {tx_input['txid']}:{tx_input['vout']}")
                
            if not self._verify_input_signature(tx_input, utxo["address"]):
                raise InvalidTransactionError(f"Invalid signature for input: {tx_input['txid']}:{tx_input['vout']}")
                
            input_sum += utxo["amount"]
        
        for output in tx["outputs"]:
            if not all(field in output for field in ["address", "amount"]):
                raise InvalidTransactionError(f"Invalid output format: {output}")
                
            if not isinstance(output["amount"], (int, float)) or output["amount"] <= 0:
                raise InvalidTransactionError(f"Invalid amount: {output['amount']}")
        
        output_sum = sum(output["amount"] for output in tx["outputs"])
        
        if input_sum < output_sum:
            raise InvalidTransactionError(f"Insufficient funds: inputs total {input_sum}, outputs total {output_sum}")
            
        return True
    
    def debug_transaction(self, tx: Dict[str, Any]) -> Dict[str, Any]:
        """Debug a transaction without adding it to the mempool."""
        debug_info = {
            "transaction": tx,
            "validation_result": "Failed",
            "error": None,
            "input_details": [],
            "output_details": {
                "total": 0,
                "outputs": []
            },
            "balance": {
                "input_total": 0,
                "output_total": 0,
                "fee": 0
            }
        }
        
        try:
            # Check transaction structure
            if not tx.get("inputs") or not tx.get("outputs"):
                debug_info["error"] = "Transaction must have inputs and outputs"
                return debug_info
            
            # Check inputs
            input_sum = 0
            for tx_input in tx["inputs"]:
                input_details = {
                    "txid": tx_input.get("txid", "Missing"),
                    "vout": tx_input.get("vout", "Missing"),
                    "found": False,
                    "spent": False,
                    "signature_valid": False,
                    "amount": 0,
                    "address": None
                }
                
                # Check input structure
                if not all(field in tx_input for field in ["txid", "vout", "signature"]):
                    input_details["error"] = "Invalid input format"
                    debug_info["input_details"].append(input_details)
                    continue
                
                # Check if UTXO exists
                utxo = self._get_utxo(tx_input["txid"], tx_input["vout"])
                if not utxo:
                    input_details["error"] = "UTXO not found"
                    debug_info["input_details"].append(input_details)
                    continue
                
                input_details["found"] = True
                input_details["amount"] = utxo["amount"]
                input_details["address"] = utxo["address"]
                
                # Check if UTXO is already spent
                if self._is_utxo_spent_in_mempool(tx_input["txid"], tx_input["vout"]):
                    input_details["spent"] = True
                    input_details["error"] = "UTXO already spent"
                    debug_info["input_details"].append(input_details)
                    continue
                
                # Check signature
                if not self._verify_input_signature(tx_input, utxo["address"]):
                    input_details["error"] = "Invalid signature"
                    debug_info["input_details"].append(input_details)
                    continue
                
                input_details["signature_valid"] = True
                input_sum += utxo["amount"]
                
                debug_info["input_details"].append(input_details)
            
            # Check outputs
            output_sum = 0
            for i, output in enumerate(tx["outputs"]):
                output_details = {
                    "index": i,
                    "address": output.get("address", "Missing"),
                    "amount": output.get("amount", 0),
                    "valid": True
                }
                
                # Check output structure
                if not all(field in output for field in ["address", "amount"]):
                    output_details["valid"] = False
                    output_details["error"] = "Invalid output format"
                    debug_info["output_details"]["outputs"].append(output_details)
                    continue
                
                # Check amount validity
                if not isinstance(output["amount"], (int, float)) or output["amount"] <= 0:
                    output_details["valid"] = False
                    output_details["error"] = "Invalid amount"
                    debug_info["output_details"]["outputs"].append(output_details)
                    continue
                
                output_sum += output["amount"]
                debug_info["output_details"]["outputs"].append(output_details)
            
            debug_info["balance"]["input_total"] = input_sum
            debug_info["balance"]["output_total"] = output_sum
            debug_info["output_details"]["total"] = output_sum
            
            # Check if inputs cover outputs
            if input_sum < output_sum:
                debug_info["error"] = f"Insufficient funds: inputs total {input_sum}, outputs total {output_sum}"
                return debug_info
            
            debug_info["balance"]["fee"] = input_sum - output_sum
            debug_info["validation_result"] = "Success"
            
            return debug_info
            
        except Exception as e:
            debug_info["error"] = f"Unexpected error: {str(e)}"
            return debug_info
    
    def _get_utxo(self, txid: str, vout: int) -> Optional[Dict[str, Any]]:
        return self.utxos.find_one({"txid": txid, "vout": vout})
    
    def _is_utxo_spent_in_mempool(self, txid: str, vout: int) -> bool:
        # Check if already marked as spent
        utxo = self._get_utxo(txid, vout)
        if utxo and utxo.get("spent_in_mempool", False):
            return True
            
        # Check references in mempool
        transactions = list(self.mempool.find({}))
        for tx in transactions:
            for tx_input in tx.get("inputs", []):
                if tx_input.get("txid") == txid and tx_input.get("vout") == vout:
                    return True
        return False
    
    def _mark_utxo_spent(self, txid: str, vout: int) -> bool:
        utxo = self._get_utxo(txid, vout)
        
        if not utxo:
            return False
        
        # Get utxo's ID
        utxo_id = utxo.get("_id")
        if not utxo_id:
            return False
            
        # Update with spent_in_mempool flag
        utxo_data = utxo.copy()
        utxo_data["spent_in_mempool"] = True
        
        # Replace the entire document to ensure the update takes effect
        self.utxos.delete({"_id": utxo_id})
        self.utxos.insert(utxo_data)
        
        # Verify the update
        updated_utxo = self._get_utxo(txid, vout)
        return updated_utxo and updated_utxo.get("spent_in_mempool", False)
    
    def _verify_input_signature(self, tx_input: Dict[str, Any], address: str) -> bool:
        try:
            from Kaidos.wallet.wallet import Wallet
            wallet = Wallet()
            result = wallet.verify_input_signature(tx_input, address)
            wallet.close()
            return result
        except Exception:
            return False
    
    def get_pending_transactions(self, limit: int = 100) -> List[Dict[str, Any]]:
        # Manually filter for pending transactions
        transactions = list(self.mempool.find({}))
        pending_transactions = [tx for tx in transactions if tx.get("status") == "pending"]
        pending_transactions.sort(key=lambda tx: tx["timestamp"])
        return pending_transactions[:limit]
    
    def get_transaction(self, txid: str) -> Optional[Dict[str, Any]]:
        return self.mempool.find_one({"txid": txid})
    
    def get_transactions_by_address(self, address: str) -> List[Dict[str, Any]]:
        # Manually check for transactions involving this address
        result = []
        transactions = list(self.mempool.find({}))
        for tx in transactions:
            for output in tx.get("outputs", []):
                if output.get("address") == address:
                    result.append(tx)
                    break
        return result
    
    def update_transaction_status(self, txid: str, status: str) -> bool:
        result = self.mempool.update(
            {"txid": txid},
            {"$set": {"status": status}}
        )
        return result > 0
    
    def remove_transactions(self, txids: List[str]) -> int:
        count = 0
        for txid in txids:
            result = self.mempool.delete({"txid": txid})
            count += result
        return count
    
    def clear_mempool(self) -> int:
        count = self.mempool.count()
        self.mempool.delete_many({})
        return count
    
    def add_utxo(self, txid: str, vout: int, address: str, amount: float) -> str:
        utxo_data = {
            "txid": txid,
            "vout": vout,
            "address": address,
            "amount": amount,
            "created_at": datetime.now().isoformat()
        }
        return self.utxos.insert(utxo_data)
    
    def remove_utxo(self, txid: str, vout: int) -> bool:
        # Verify UTXO existence
        utxo = self._get_utxo(txid, vout)
        if not utxo:
            return False
        
        # Delete using the document ID if available for more reliable deletion
        if "_id" in utxo:
            self.utxos.delete({"_id": utxo["_id"]})
        
        # Also delete with txid/vout for certainty
        self.utxos.delete({"txid": txid, "vout": vout})
        
        # For a more aggressive deletion approach
        self.utxos.delete_many({"txid": txid, "vout": vout})
        
        # Verify the deletion worked
        return self._get_utxo(txid, vout) is None
    
    def get_utxos_for_address(self, address: str) -> List[Dict[str, Any]]:
        return list(self.utxos.find({"address": address}))
    
    def get_balance(self, address: str) -> float:
        utxos = self.get_utxos_for_address(address)
        return sum(utxo["amount"] for utxo in utxos)
    
    def create_coinbase_transaction(self, miner_address: str, reward: float, fees: float = 0) -> Dict[str, Any]:
        tx_data = {
            "txid": self._generate_coinbase_txid(miner_address, reward + fees),
            "inputs": [],
            "outputs": [
                {
                    "address": miner_address,
                    "amount": reward + fees
                }
            ],
            "timestamp": datetime.now().isoformat(),
            "coinbase": True
        }
        return tx_data
    
    def _generate_coinbase_txid(self, miner_address: str, amount: float) -> str:
        import hashlib
        
        data = f"{miner_address}:{amount}:{datetime.now().isoformat()}"
        return hashlib.sha256(data.encode()).hexdigest()
    
    def process_block_transactions(self, block: Dict[str, Any]) -> None:
        for tx in block["transactions"]:
            if not tx.get("coinbase", False):
                for tx_input in tx["inputs"]:
                    utxo = self._get_utxo(tx_input["txid"], tx_input["vout"])
                    if utxo:
                        utxo_id = utxo.get("_id")
                        if utxo_id:
                            self.utxos.delete({"_id": utxo_id})
                        
                        self.utxos.delete({"txid": tx_input["txid"], "vout": tx_input["vout"]})
                        self.utxos.delete_many({"txid": tx_input["txid"], "vout": tx_input["vout"]})
            
            for i, output in enumerate(tx["outputs"]):
                self.add_utxo(tx["txid"], i, output["address"], output["amount"])
            
            self.mempool.delete({"txid": tx["txid"]})
    
    def calculate_transaction_fee(self, tx: Dict[str, Any]) -> float:
        if tx.get("coinbase", False):
            return 0
            
        input_sum = 0
        for tx_input in tx["inputs"]:
            utxo = self._get_utxo(tx_input["txid"], tx_input["vout"])
            if utxo:
                input_sum += utxo["amount"]
        
        output_sum = sum(output["amount"] for output in tx["outputs"])
        
        return max(0, input_sum - output_sum)
    
    def close(self) -> None:
        self.db.close()

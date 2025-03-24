import os
import json
import base64
from datetime import datetime
from typing import Dict, Any, Optional, Tuple, List
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.backends import default_backend
from zenithdb import Database

from Kaidos.core.exceptions import KeyGenerationError, SignatureError


class Wallet:
    
    def __init__(self, db_path: str = "kaidos_wallets.db"):
        self.db = Database(db_path)
        self.wallets = self.db.collection("wallets")
        self.addresses = self.db.collection("addresses")
        self._setup_indexes()
    
    def _setup_indexes(self) -> None:
        self.db.create_index("wallets", "wallet_id", unique=True)
        self.db.create_index("addresses", "address", unique=True)
        self.db.create_index("addresses", "wallet_id")
        self.db.create_index("addresses", "public_key")
    
    def create_wallet(self, passphrase: Optional[str] = None) -> Dict[str, str]:
        try:
            import uuid
            
            # Generate a unique wallet ID
            wallet_id = str(uuid.uuid4())
            
            # Create wallet record
            wallet_data = {
                "wallet_id": wallet_id,
                "name": f"Wallet-{wallet_id[:8]}",
                "created_at": datetime.now().isoformat(),
                "encrypted": passphrase is not None
            }
            
            # Insert wallet
            self.wallets.insert(wallet_data)
            
            # Create initial address for this wallet
            address_data = self.create_address(wallet_id, passphrase)
            
            # Return combined wallet info
            return {
                "wallet_id": wallet_id,
                "address": address_data["address"],
                "public_key": address_data["public_key"]
            }
            
        except Exception as e:
            raise KeyGenerationError(f"Failed to generate wallet: {str(e)}")
    
    def create_address(self, wallet_id: str, passphrase: Optional[str] = None) -> Dict[str, str]:
        try:
            # Check if wallet exists
            wallet = self.wallets.find_one({"wallet_id": wallet_id})
            if not wallet:
                raise KeyGenerationError(f"Wallet not found: {wallet_id}")
            
            # Generate RSA key pair
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
                backend=default_backend()
            )
            public_key = private_key.public_key()
            
            # Generate address from public key
            address = self._generate_address(public_key)
            
            # Serialize keys
            public_pem = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ).decode('utf-8')
            
            # Encrypt private key if wallet is encrypted
            if wallet.get("encrypted", False):
                if not passphrase:
                    raise KeyGenerationError("Passphrase required for encrypted wallet")
                encryption_algorithm = serialization.BestAvailableEncryption(
                    passphrase.encode('utf-8')
                )
            else:
                encryption_algorithm = serialization.NoEncryption()
                
            private_pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=encryption_algorithm
            ).decode('utf-8')
            
            # Store address in database
            address_data = {
                "wallet_id": wallet_id,
                "address": address,
                "public_key": public_pem,
                "private_key": private_pem,
                "created_at": datetime.now().isoformat()
            }
            
            self.addresses.insert(address_data)
            
            # Return address info (excluding private key)
            return {
                "address": address,
                "public_key": public_pem
            }
            
        except KeyGenerationError:
            raise
        except Exception as e:
            raise KeyGenerationError(f"Failed to generate address: {str(e)}")
    
    def _generate_address(self, public_key) -> str:
        # Get public key bytes
        key_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        # Hash the public key
        digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
        digest.update(key_bytes)
        hash_bytes = digest.finalize()
        
        # Take first 20 bytes of hash and encode as base64
        address_bytes = hash_bytes[:20]
        address = base64.b32encode(address_bytes).decode('utf-8')
        
        # Add 'KD' prefix to identify as Kaidos address
        return f"KD{address}"
    
    def get_wallet(self, wallet_id: str) -> Optional[Dict[str, Any]]:
        return self.wallets.find_one({"wallet_id": wallet_id})
    
    def get_wallet_by_address(self, address: str) -> Optional[Dict[str, Any]]:
        address_data = self.addresses.find_one({"address": address})
        if not address_data:
            return None
            
        return self.wallets.find_one({"wallet_id": address_data["wallet_id"]})
    
    def list_wallets(self) -> list:
        wallets = list(self.wallets.find({}))
        result = []
        
        for wallet in wallets:
            wallet_id = wallet["wallet_id"]
            addresses = list(self.addresses.find({"wallet_id": wallet_id}))
            
            # Remove private keys from addresses
            for addr in addresses:
                addr.pop("private_key", None)
            
            wallet["addresses"] = addresses
            result.append(wallet)
            
        return result
    
    def list_addresses(self, wallet_id: str) -> list:
        addresses = list(self.addresses.find({"wallet_id": wallet_id}))
        
        # Remove private keys
        for addr in addresses:
            addr.pop("private_key", None)
            
        return addresses
    
    def sign_transaction_input(
        self,
        txid: str,
        vout: int,
        address: str,
        passphrase: Optional[str] = None
    ) -> str:
        try:
            # Get address data
            address_data = self.addresses.find_one({"address": address})
            if not address_data:
                raise SignatureError(f"Address not found: {address}")
            
            # Get wallet
            wallet = self.wallets.find_one({"wallet_id": address_data["wallet_id"]})
            if not wallet:
                raise SignatureError(f"Wallet not found for address: {address}")
            
            # Load private key
            private_key = self._load_private_key(address_data, passphrase, wallet.get("encrypted", False))
            
            # Create message to sign
            message = f"{txid}:{vout}".encode('utf-8')
            
            # Sign message
            signature = private_key.sign(
                message,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            
            # Encode signature as base64
            return base64.b64encode(signature).decode('utf-8')
            
        except SignatureError:
            raise
        except Exception as e:
            raise SignatureError(f"Failed to sign transaction input: {str(e)}")
    
    def create_transaction(
        self,
        sender_address: str,
        recipient_address: str,
        amount: float,
        passphrase: Optional[str] = None
    ) -> Dict[str, Any]:
        try:
            # Get UTXOs for sender from all possible database paths
            from Kaidos.core.transaction_manager import TransactionManager
            db_paths = ["kaidos_chain.db", "kaidos_node.db"]
            all_utxos = []
            utxo_db_path = None
            
            for db_path in db_paths:
                tx_manager = TransactionManager(db_path)
                utxos = tx_manager.get_utxos_for_address(sender_address)
                if utxos:
                    all_utxos.extend(utxos)
                    if not utxo_db_path:  # Remember the first DB that has UTXOs
                        utxo_db_path = db_path
                tx_manager.close()
            
            if not all_utxos:
                raise SignatureError(f"No UTXOs found for address: {sender_address}")
            
            # Calculate total available
            total_available = sum(utxo["amount"] for utxo in all_utxos)
            
            if total_available < amount:
                raise SignatureError(f"Insufficient funds: {total_available} < {amount}")
            
            # Select UTXOs to use
            selected_utxos = []
            selected_amount = 0
            
            for utxo in all_utxos:
                selected_utxos.append(utxo)
                selected_amount += utxo["amount"]
                if selected_amount >= amount:
                    break
            
            # Create inputs
            inputs = []
            for utxo in selected_utxos:
                signature = self.sign_transaction_input(
                    utxo["txid"],
                    utxo["vout"],
                    sender_address,
                    passphrase
                )
                
                inputs.append({
                    "txid": utxo["txid"],
                    "vout": utxo["vout"],
                    "signature": signature
                })
            
            # Create outputs
            outputs = [
                {
                    "address": recipient_address,
                    "amount": amount
                }
            ]
            
            # Add change output if necessary
            change = selected_amount - amount
            if change > 0:
                outputs.append({
                    "address": sender_address,
                    "amount": change
                })
            
            # Create transaction
            tx_data = {
                "inputs": inputs,
                "outputs": outputs
            }
            
            # Use the database that had the UTXOs to add the transaction
            tx_manager = TransactionManager(utxo_db_path or "kaidos_chain.db")
            
            # Add to mempool
            tx_id = tx_manager.add_transaction(
                inputs,
                outputs,
                ""
            )
            
            tx_manager.close()
            
            # Add txid to transaction data
            tx_data["txid"] = tx_id
            
            return tx_data
            
        except SignatureError:
            raise
        except Exception as e:
            raise SignatureError(f"Failed to create transaction: {str(e)}")
    
    def _load_private_key(self, address_data: Dict[str, Any], passphrase: Optional[str] = None, is_encrypted: bool = False):
        private_key_pem = address_data["private_key"]
        
        # Decrypt private key if encrypted
        if is_encrypted:
            if not passphrase:
                raise SignatureError("Passphrase required for encrypted wallet")
                
            try:
                return serialization.load_pem_private_key(
                    private_key_pem.encode('utf-8'),
                    password=passphrase.encode('utf-8'),
                    backend=default_backend()
                )
            except Exception:
                raise SignatureError("Invalid passphrase")
        else:
            return serialization.load_pem_private_key(
                private_key_pem.encode('utf-8'),
                password=None,
                backend=default_backend()
            )
    
    def verify_input_signature(self, tx_input: Dict[str, Any], address: str) -> bool:
        try:
            # Get address data
            address_data = self.addresses.find_one({"address": address})
            if not address_data:
                return False
            
            # Load public key
            public_key = serialization.load_pem_public_key(
                address_data["public_key"].encode('utf-8'),
                backend=default_backend()
            )
            
            # Extract signature
            signature = base64.b64decode(tx_input["signature"])
            
            # Create message
            message = f"{tx_input['txid']}:{tx_input['vout']}".encode('utf-8')
            
            # Verify signature
            public_key.verify(
                signature,
                message,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            
            return True
            
        except Exception:
            return False
    
    def get_balance(self, address: str) -> float:
        from Kaidos.core.transaction_manager import TransactionManager
        db_paths = ["kaidos_chain.db", "kaidos_node.db"]
        total_balance = 0.0
        
        for db_path in db_paths:
            tx_manager = TransactionManager(db_path)
            balance = tx_manager.get_balance(address)
            total_balance += balance
            tx_manager.close()
            
        return total_balance
    
    def close(self) -> None:
        self.db.close()

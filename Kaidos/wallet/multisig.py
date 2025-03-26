import base64
import hashlib
import json
from typing import List, Dict, Any, Optional, Tuple

from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.backends import default_backend

from Kaidos.core.exceptions import SignatureError


class MultiSigWallet:
    """Multi-signature wallet implementation."""
    
    @staticmethod
    def create_multisig_address(public_keys: List[str], m: int) -> str:
        """Create a multi-signature address requiring m-of-n signatures."""
        if m <= 0 or m > len(public_keys):
            raise ValueError(f"Required signatures (m={m}) must be between 1 and {len(public_keys)}")
            
        # Sort public keys for consistent address generation
        sorted_keys = sorted(public_keys)
        
        # Create a hash of all public keys and the required signatures
        multisig_data = {
            "public_keys": sorted_keys,
            "required_signatures": m
        }
        
        data_string = json.dumps(multisig_data, sort_keys=True)
        hash_bytes = hashlib.sha256(data_string.encode()).digest()
        
        # Take first 20 bytes of hash and encode as base64
        address_bytes = hash_bytes[:20]
        address = base64.b32encode(address_bytes).decode('utf-8')
        
        # Add 'KDM' prefix to identify as Kaidos multi-signature address
        return f"KDM{address}"
    
    @staticmethod
    def sign_transaction_input(
        txid: str,
        vout: int,
        private_key_pem: str,
        passphrase: Optional[str] = None
    ) -> str:
        """Sign a transaction input with a private key."""
        try:
            # Load private key
            if passphrase:
                private_key = serialization.load_pem_private_key(
                    private_key_pem.encode('utf-8'),
                    password=passphrase.encode('utf-8'),
                    backend=default_backend()
                )
            else:
                private_key = serialization.load_pem_private_key(
                    private_key_pem.encode('utf-8'),
                    password=None,
                    backend=default_backend()
                )
            
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
            
        except Exception as e:
            raise SignatureError(f"Failed to sign transaction input: {str(e)}")
    
    @staticmethod
    def verify_multisig_transaction(
        tx_input: Dict[str, Any],
        multisig_data: Dict[str, Any]
    ) -> bool:
        """Verify a multi-signature transaction input."""
        try:
            # Extract data
            txid = tx_input["txid"]
            vout = tx_input["vout"]
            signatures = tx_input.get("signatures", [])
            public_keys = multisig_data["public_keys"]
            required_signatures = multisig_data["required_signatures"]
            
            # Check if we have enough signatures
            if len(signatures) < required_signatures:
                return False
                
            # Create message that was signed
            message = f"{txid}:{vout}".encode('utf-8')
            
            # Count valid signatures
            valid_signatures = 0
            used_keys = set()
            
            for signature_data in signatures:
                signature = base64.b64decode(signature_data["signature"])
                key_index = signature_data["key_index"]
                
                # Prevent using the same key twice
                if key_index in used_keys or key_index >= len(public_keys):
                    continue
                    
                # Load public key
                public_key = serialization.load_pem_public_key(
                    public_keys[key_index].encode('utf-8'),
                    backend=default_backend()
                )
                
                try:
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
                    
                    # Signature is valid
                    valid_signatures += 1
                    used_keys.add(key_index)
                    
                    # If we have enough valid signatures, return True
                    if valid_signatures >= required_signatures:
                        return True
                        
                except Exception:
                    # Signature verification failed, continue with next signature
                    continue
                    
            # Not enough valid signatures
            return False
            
        except Exception:
            return False
    
    @staticmethod
    def create_multisig_transaction_input(
        txid: str,
        vout: int,
        signatures: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Create a multi-signature transaction input."""
        return {
            "txid": txid,
            "vout": vout,
            "signatures": signatures,
            "multisig": True
        }
    
    @staticmethod
    def get_multisig_data(address: str, public_keys: List[str], m: int) -> Dict[str, Any]:
        """Get multi-signature data for an address."""
        # Verify the address matches the public keys and m
        computed_address = MultiSigWallet.create_multisig_address(public_keys, m)
        if computed_address != address:
            raise ValueError("Address does not match public keys and required signatures")
            
        return {
            "address": address,
            "public_keys": public_keys,
            "required_signatures": m
        }

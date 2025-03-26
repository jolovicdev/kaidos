import argparse
import getpass
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional

from Kaidos.wallet.wallet import Wallet
from Kaidos.core.exceptions import KeyGenerationError, SignatureError


def create_wallet(args: argparse.Namespace) -> None:
    wallet = Wallet()
    
    try:
        # Check if passphrase is required
        passphrase = None
        if args.encrypted:
            passphrase = getpass.getpass("Enter passphrase: ")
            confirm = getpass.getpass("Confirm passphrase: ")
            
            if passphrase != confirm:
                print("Error: Passphrases do not match")
                sys.exit(1)
        
        # Create wallet
        result = wallet.create_wallet(passphrase)
        
        print(f"Wallet created successfully!")
        print(f"Wallet ID: {result['wallet_id']}")
        print(f"Address: {result['address']}")
        print("IMPORTANT: Keep your wallet ID and address safe. You will need them for future operations.")
        
        if args.encrypted:
            print("Your wallet is encrypted. You will need your passphrase for transactions.")
        else:
            print("Your wallet is not encrypted. Anyone with access to the database can use it.")
            
    except KeyGenerationError as e:
        print(f"Error creating wallet: {str(e)}")
        sys.exit(1)
    finally:
        wallet.close()


def list_wallets(args: argparse.Namespace) -> None:
    wallet = Wallet()
    
    try:
        wallets = wallet.list_wallets()
        
        if not wallets:
            print("No wallets found")
            return
            
        print(f"Found {len(wallets)} wallets:")
        for w in wallets:
            print(f"  Wallet ID: {w['wallet_id']}")
            print(f"  Name: {w.get('name', 'Unnamed Wallet')}")
            print(f"  Encrypted: {w.get('encrypted', False)}")
            print(f"  Created: {w.get('created_at', 'Unknown')}")
            
            # Display addresses for this wallet
            if 'addresses' in w and w['addresses']:
                print(f"  Addresses ({len(w['addresses'])}):")
                total_balance = 0
                for addr in w['addresses']:
                    balance = wallet.get_balance(addr['address'])
                    total_balance += balance
                    print(f"    - {addr['address']} (Balance: {balance})")
                print(f"  Total Balance: {total_balance}")
            else:
                print("  No addresses found")
            print()
            
    finally:
        wallet.close()


def get_balance(args: argparse.Namespace) -> None:
    wallet = Wallet()
    
    try:
        balance = wallet.get_balance(args.address)
        print(f"Balance for {args.address}: {balance}")
    finally:
        wallet.close()


def create_transaction(args: argparse.Namespace) -> None:
    wallet = Wallet()
    
    try:
        # Get address data
        address_data = wallet.addresses.find_one({"address": args.sender})
        if not address_data:
            print(f"Error: Sender address not found: {args.sender}")
            sys.exit(1)
            
        # Get wallet
        w = wallet.get_wallet(address_data["wallet_id"])
        if not w:
            print(f"Error: Wallet not found for address: {args.sender}")
            sys.exit(1)
            
        # Check if wallet is encrypted
        if w.get('encrypted', False):
            passphrase = getpass.getpass("Enter passphrase: ")
        else:
            passphrase = None
        
        # Create transaction
        tx = wallet.create_transaction(
            args.sender,
            args.recipient,
            args.amount,
            passphrase
        )
        
        # Print transaction details
        print("Transaction created successfully:")
        print(f"  Transaction ID: {tx['txid']}")
        print(f"  Inputs: {len(tx['inputs'])}")
        for i, input_data in enumerate(tx['inputs']):
            print(f"    Input {i+1}: {input_data['txid'][:8]}...:{input_data['vout']}")
        
        print(f"  Outputs: {len(tx['outputs'])}")
        for i, output in enumerate(tx['outputs']):
            print(f"    Output {i+1}: {output['address']} - {output['amount']}")
        
        # Save to file if requested
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(tx, f, indent=2)
            print(f"Transaction saved to {args.output}")
        
    except SignatureError as e:
        print(f"Error creating transaction: {str(e)}")
        sys.exit(1)
    finally:
        wallet.close()


def get_utxos(args: argparse.Namespace) -> None:
    from Kaidos.core.transaction_manager import TransactionManager
    tx_manager = TransactionManager()
    
    try:
        utxos = tx_manager.get_utxos_for_address(args.address)
        
        if not utxos:
            print(f"No UTXOs found for {args.address}")
            return
            
        print(f"Found {len(utxos)} UTXOs for {args.address}:")
        total = 0
        for utxo in utxos:
            print(f"  TXID: {utxo['txid'][:8]}...:{utxo['vout']}")
            print(f"  Amount: {utxo['amount']}")
            print(f"  Created: {utxo['created_at']}")
            print()
            total += utxo['amount']
            
        print(f"Total balance: {total}")
        
    finally:
        tx_manager.close()


def create_address(args: argparse.Namespace) -> None:
    wallet = Wallet()
    
    try:
        # Check if wallet is encrypted
        w = wallet.get_wallet(args.wallet_id)
        if not w:
            print(f"Error: Wallet not found with ID: {args.wallet_id}")
            sys.exit(1)
            
        if w.get('encrypted', False):
            passphrase = getpass.getpass("Enter passphrase: ")
        else:
            passphrase = None
        
        # Create address
        result = wallet.create_address(args.wallet_id, passphrase)
        
        print(f"Address created successfully!")
        print(f"Address: {result['address']}")
        print("IMPORTANT: Keep your address safe. You will need it to receive funds.")
            
    except KeyGenerationError as e:
        print(f"Error creating address: {str(e)}")
        sys.exit(1)
    finally:
        wallet.close()


def list_addresses(args: argparse.Namespace) -> None:
    wallet = Wallet()
    
    try:
        # Check if wallet exists
        w = wallet.get_wallet(args.wallet_id)
        if not w:
            print(f"Error: Wallet not found with ID: {args.wallet_id}")
            sys.exit(1)
            
        addresses = wallet.list_addresses(args.wallet_id)
        
        if not addresses:
            print(f"No addresses found for wallet: {args.wallet_id}")
            return
            
        print(f"Found {len(addresses)} addresses for wallet {args.wallet_id}:")
        for addr in addresses:
            print(f"  Address: {addr['address']}")
            balance = wallet.get_balance(addr['address'])
            print(f"  Balance: {balance}")
            print(f"  Created: {addr.get('created_at', 'Unknown')}")
            print()
            
    finally:
        wallet.close()


def create_multisig(args: argparse.Namespace) -> None:
    wallet = Wallet()
    
    try:
        # Parse public keys
        public_keys = []
        for key_file in args.public_keys:
            with open(key_file, 'r') as f:
                public_keys.append(f.read().strip())
        
        # Create multisig address
        from Kaidos.wallet.multisig import MultiSigWallet
        address = MultiSigWallet.create_multisig_address(public_keys, args.required)
        
        # Store multisig data in database
        multisig_data = {
            "address": address,
            "public_keys": public_keys,
            "required_signatures": args.required,
            "created_at": datetime.now().isoformat()
        }
        
        wallet.db.collection("multisig").insert(multisig_data)
        
        print(f"Multi-signature address created successfully!")
        print(f"Address: {address}")
        print(f"Required signatures: {args.required} of {len(public_keys)}")
        print("IMPORTANT: Keep this address and the public keys safe.")
        
    except Exception as e:
        print(f"Error creating multi-signature address: {str(e)}")
        sys.exit(1)
    finally:
        wallet.close()


def sign_multisig_tx(args: argparse.Namespace) -> None:
    wallet = Wallet()
    
    try:
        # Load transaction from file
        with open(args.transaction, 'r') as f:
            tx_data = json.load(f)
        
        # Get wallet for the key
        address_data = wallet.addresses.find_one({"address": args.address})
        if not address_data:
            print(f"Error: Address not found: {args.address}")
            sys.exit(1)
            
        # Get wallet
        w = wallet.get_wallet(address_data["wallet_id"])
        if not w:
            print(f"Error: Wallet not found for address: {args.address}")
            sys.exit(1)
            
        # Check if wallet is encrypted
        if w.get('encrypted', False):
            passphrase = getpass.getpass("Enter passphrase: ")
        else:
            passphrase = None
        
        # Find the input to sign
        input_idx = -1
        for i, tx_input in enumerate(tx_data.get("inputs", [])):
            if tx_input.get("txid") == args.txid and tx_input.get("vout") == args.vout:
                input_idx = i
                break
                
        if input_idx == -1:
            print(f"Error: Input {args.txid}:{args.vout} not found in transaction")
            sys.exit(1)
            
        # Sign the input
        from Kaidos.wallet.multisig import MultiSigWallet
        signature = MultiSigWallet.sign_transaction_input(
            args.txid,
            args.vout,
            address_data["private_key"],
            passphrase
        )
        
        # Add signature to transaction
        if "signatures" not in tx_data["inputs"][input_idx]:
            tx_data["inputs"][input_idx]["signatures"] = []
            tx_data["inputs"][input_idx]["multisig"] = True
            
        # Add signature with key index
        tx_data["inputs"][input_idx]["signatures"].append({
            "signature": signature,
            "key_index": args.key_index
        })
        
        # Save updated transaction
        with open(args.output or args.transaction, 'w') as f:
            json.dump(tx_data, f, indent=2)
            
        print(f"Transaction signed successfully!")
        print(f"Signature added for input {args.txid}:{args.vout} with key index {args.key_index}")
        print(f"Transaction saved to {args.output or args.transaction}")
        
    except Exception as e:
        print(f"Error signing transaction: {str(e)}")
        sys.exit(1)
    finally:
        wallet.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Kaidos Wallet CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Create wallet command
    create_parser = subparsers.add_parser("create", help="Create a new wallet")
    create_parser.add_argument(
        "--encrypted", 
        action="store_true", 
        help="Encrypt the wallet with a passphrase"
    )
    
    # List wallets command
    list_parser = subparsers.add_parser("list", help="List all wallets")
    
    # Get balance command
    balance_parser = subparsers.add_parser("balance", help="Get wallet balance")
    balance_parser.add_argument("address", help="Wallet address")
    
    # Create new address command
    address_parser = subparsers.add_parser("address", help="Create a new address for a wallet")
    address_parser.add_argument("wallet_id", help="Wallet ID")
    
    # List addresses command
    list_addresses_parser = subparsers.add_parser("addresses", help="List all addresses for a wallet")
    list_addresses_parser.add_argument("wallet_id", help="Wallet ID")
    
    # Create transaction command
    tx_parser = subparsers.add_parser("tx", help="Create a transaction")
    tx_parser.add_argument("sender", help="Sender wallet address")
    tx_parser.add_argument("recipient", help="Recipient wallet address")
    tx_parser.add_argument("amount", type=float, help="Transaction amount")
    tx_parser.add_argument(
        "--output", "-o",
        help="Output file to save transaction (JSON)"
    )
    
    # Get UTXOs command
    utxos_parser = subparsers.add_parser("utxos", help="Get UTXOs for a wallet")
    utxos_parser.add_argument("address", help="Wallet address")
    
    # Create multi-signature address command
    multisig_parser = subparsers.add_parser("multisig", help="Create a multi-signature address")
    multisig_parser.add_argument(
        "--required", "-r",
        type=int,
        required=True,
        help="Number of required signatures"
    )
    multisig_parser.add_argument(
        "--public-keys", "-p",
        nargs="+",
        required=True,
        help="Files containing public keys"
    )
    
    # Sign multi-signature transaction command
    sign_multisig_parser = subparsers.add_parser("sign-multisig", help="Sign a multi-signature transaction")
    sign_multisig_parser.add_argument("transaction", help="Transaction file (JSON)")
    sign_multisig_parser.add_argument("address", help="Signing address")
    sign_multisig_parser.add_argument("txid", help="Transaction input ID")
    sign_multisig_parser.add_argument("vout", type=int, help="Transaction input vout")
    sign_multisig_parser.add_argument("key_index", type=int, help="Index of the key in the multisig address")
    sign_multisig_parser.add_argument(
        "--output", "-o",
        help="Output file to save signed transaction (JSON)"
    )
    
    args = parser.parse_args()
    
    if args.command == "create":
        create_wallet(args)
    elif args.command == "list":
        list_wallets(args)
    elif args.command == "balance":
        get_balance(args)
    elif args.command == "address":
        create_address(args)
    elif args.command == "addresses":
        list_addresses(args)
    elif args.command == "tx":
        create_transaction(args)
    elif args.command == "utxos":
        get_utxos(args)
    elif args.command == "multisig":
        create_multisig(args)
    elif args.command == "sign-multisig":
        sign_multisig_tx(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

import argparse
import sys
import json
import requests
from typing import Dict, Any, Optional

from Kaidos.network.node import Node
from Kaidos.core.blockchain import Blockchain
from Kaidos.core.transaction_manager import TransactionManager
from Kaidos.core.exceptions import InvalidBlockError, InvalidTransactionError


def init_node(args: argparse.Namespace) -> None:
    try:
        # Initialize blockchain
        blockchain = Blockchain()
        
        # Check if blockchain is valid
        if blockchain.is_chain_valid():
            print("Blockchain initialized successfully")
            print(f"Genesis block created with hash: {blockchain.get_block_by_index(0)['hash']}")
        else:
            print("Error: Blockchain validation failed")
            sys.exit(1)
            
    except Exception as e:
        print(f"Error initializing node: {str(e)}")
        sys.exit(1)
    finally:
        blockchain.close()


def start_node(args: argparse.Namespace) -> None:
    try:
        host = args.host
        port = args.port
        
        print(f"Starting Kaidos node on {host}:{port}...")
        node = Node(host=host, port=port)
        node.start()
        
    except Exception as e:
        print(f"Error starting node: {str(e)}")
        sys.exit(1)


def add_peer(args: argparse.Namespace) -> None:
    try:
        # Connect to local node
        response = requests.post(
            f"http://{args.node}/peers",
            json={"address": args.peer}
        )
        
        if response.status_code == 200:
            print(f"Peer {args.peer} added successfully")
        else:
            print(f"Error adding peer: {response.json().get('error', 'Unknown error')}")
            sys.exit(1)
            
    except requests.RequestException as e:
        print(f"Error connecting to node: {str(e)}")
        sys.exit(1)


def list_peers(args: argparse.Namespace) -> None:
    try:
        # Connect to local node
        response = requests.get(f"http://{args.node}/peers")
        
        if response.status_code == 200:
            peers = response.json()["peers"]
            
            if not peers:
                print("No peers found")
                return
                
            print(f"Found {len(peers)} peers:")
            for peer in peers:
                print(f"  Address: {peer['address']}")
                print(f"  Last seen: {peer.get('last_seen', 'Never')}")
                print()
        else:
            print(f"Error listing peers: {response.json().get('error', 'Unknown error')}")
            sys.exit(1)
            
    except requests.RequestException as e:
        print(f"Error connecting to node: {str(e)}")
        sys.exit(1)


def mine_block(args: argparse.Namespace) -> None:
    try:
        # Connect to local node
        response = requests.post(
            f"http://{args.node}/blocks/mine",
            json={"miner_address": args.address}
        )
        
        if response.status_code == 200:
            result = response.json()
            block = result["block"]
            reward = result["reward"]
            
            print(f"Block mined successfully:")
            print(f"  Index: {block['index']}")
            print(f"  Hash: {block['hash']}")
            print(f"  Transactions: {len(block['transactions'])}")
            print(f"  Miner: {block['miner_address']}")
            print(f"  Reward: {reward}")
            print(f"  Nonce: {block['nonce']}")
        else:
            print(f"Error mining block: {response.json().get('error', 'Unknown error')}")
            sys.exit(1)
            
    except requests.RequestException as e:
        print(f"Error connecting to node: {str(e)}")
        sys.exit(1)


def get_blocks(args: argparse.Namespace) -> None:
    try:
        # Connect to local node
        url = f"http://{args.node}/blocks"
        if args.start is not None or args.end is not None:
            params = {}
            if args.start is not None:
                params["start"] = args.start
            if args.end is not None:
                params["end"] = args.end
            response = requests.get(url, params=params)
        else:
            response = requests.get(url)
        
        if response.status_code == 200:
            blocks = response.json()["blocks"]
            
            if not blocks:
                print("No blocks found")
                return
                
            print(f"Found {len(blocks)} blocks:")
            for block in blocks:
                print(f"  Index: {block['index']}")
                print(f"  Hash: {block['hash']}")
                print(f"  Previous hash: {block['previous_hash']}")
                print(f"  Transactions: {len(block['transactions'])}")
                if block.get('miner_address'):
                    print(f"  Miner: {block['miner_address']}")
                print(f"  Timestamp: {block['timestamp']}")
                print()
        else:
            print(f"Error getting blocks: {response.json().get('error', 'Unknown error')}")
            sys.exit(1)
            
    except requests.RequestException as e:
        print(f"Error connecting to node: {str(e)}")
        sys.exit(1)


def get_transactions(args: argparse.Namespace) -> None:
    try:
        # Connect to local node
        response = requests.get(f"http://{args.node}/transactions")
        
        if response.status_code == 200:
            transactions = response.json()["transactions"]
            
            if not transactions:
                print("No pending transactions found")
                return
                
            print(f"Found {len(transactions)} pending transactions:")
            for tx in transactions:
                print(f"  ID: {tx['txid']}")
                print(f"  Inputs: {len(tx['inputs'])}")
                print(f"  Outputs: {len(tx['outputs'])}")
                print(f"  Status: {tx['status']}")
                print()
        else:
            print(f"Error getting transactions: {response.json().get('error', 'Unknown error')}")
            sys.exit(1)
            
    except requests.RequestException as e:
        print(f"Error connecting to node: {str(e)}")
        sys.exit(1)


def debug_transaction(args: argparse.Namespace) -> None:
    try:
        # Load transaction from file
        with open(args.file, "r") as f:
            transaction = json.load(f)
        
        # Connect to local node
        response = requests.post(
            f"http://{args.node}/debug/transaction",
            json=transaction
        )
        
        if response.status_code == 200:
            debug_info = response.json()["validation_result"]
            print("Transaction Debug Information:")
            
            if debug_info["validation_result"] == "Success":
                print("✅ Transaction is valid")
            else:
                print("❌ Transaction has errors:")
                if debug_info["error"]:
                    print(f"  Error: {debug_info['error']}")
            
            # Print input details
            print("\nInputs:")
            if not debug_info["input_details"]:
                print("  No inputs found")
            else:
                for i, input_info in enumerate(debug_info["input_details"]):
                    print(f"  Input {i+1}:")
                    print(f"    TXID: {input_info['txid']}")
                    print(f"    Vout: {input_info['vout']}")
                    
                    if input_info.get("error"):
                        print(f"    ❌ Error: {input_info['error']}")
                    else:
                        print(f"    Found: {'✅' if input_info['found'] else '❌'}")
                        if input_info['found']:
                            print(f"    Amount: {input_info['amount']}")
                            print(f"    Address: {input_info['address']}")
                            print(f"    Already spent: {'❌ Yes' if input_info['spent'] else '✅ No'}")
                            print(f"    Signature valid: {'✅' if input_info['signature_valid'] else '❌'}")
            
            # Print output details
            print("\nOutputs:")
            if not debug_info["output_details"]["outputs"]:
                print("  No outputs found")
            else:
                for output_info in debug_info["output_details"]["outputs"]:
                    print(f"  Output {output_info['index']+1}:")
                    print(f"    Address: {output_info['address']}")
                    print(f"    Amount: {output_info['amount']}")
                    
                    if not output_info["valid"]:
                        print(f"    ❌ Error: {output_info.get('error', 'Invalid output')}")
            
            # Print balance details
            print("\nBalance:")
            print(f"  Total inputs: {debug_info['balance']['input_total']}")
            print(f"  Total outputs: {debug_info['balance']['output_total']}")
            
            # Check if inputs cover outputs
            if debug_info["balance"]["input_total"] >= debug_info["balance"]["output_total"]:
                print(f"  ✅ Sufficient funds (Fee: {debug_info['balance']['fee']})")
            else:
                print(f"  ❌ Insufficient funds (Shortfall: {debug_info['balance']['output_total'] - debug_info['balance']['input_total']})")
                
        else:
            print(f"Error debugging transaction: {response.json().get('error', 'Unknown error')}")
            sys.exit(1)
            
    except FileNotFoundError:
        print(f"Error: Transaction file not found: {args.file}")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in transaction file: {args.file}")
        sys.exit(1)
    except requests.RequestException as e:
        print(f"Error connecting to node: {str(e)}")
        sys.exit(1)


def send_transaction(args: argparse.Namespace) -> None:
    try:
        # Load transaction from file
        with open(args.file, "r") as f:
            transaction = json.load(f)
        
        # Connect to local node
        response = requests.post(
            f"http://{args.node}/transactions",
            json=transaction
        )
        
        if response.status_code == 200:
            tx_id = response.json()["transaction_id"]
            print(f"Transaction sent successfully")
            print(f"Transaction ID: {tx_id}")
        else:
            error_msg = response.json().get('error', 'Unknown error')
            print(f"Error sending transaction: {error_msg}")
            print("\nTry running with 'debug' command to get more information:")
            print(f"  kaidos-node debug {args.file} --node {args.node}")
            sys.exit(1)
            
    except FileNotFoundError:
        print(f"Error: Transaction file not found: {args.file}")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in transaction file: {args.file}")
        sys.exit(1)
    except requests.RequestException as e:
        print(f"Error connecting to node: {str(e)}")
        sys.exit(1)


def get_utxos(args: argparse.Namespace) -> None:
    try:
        # Connect to local node
        response = requests.get(f"http://{args.node}/utxos/{args.address}")
        
        if response.status_code == 200:
            result = response.json()
            utxos = result["utxos"]
            balance = result["balance"]
            
            if not utxos:
                print(f"No UTXOs found for {args.address}")
                return
                
            print(f"Found {len(utxos)} UTXOs for {args.address}:")
            for utxo in utxos:
                print(f"  TXID: {utxo['txid'][:8]}...:{utxo['vout']}")
                print(f"  Amount: {utxo['amount']}")
                print(f"  Created: {utxo['created_at']}")
                print()
                
            print(f"Total balance: {balance}")
        else:
            print(f"Error getting UTXOs: {response.json().get('error', 'Unknown error')}")
            sys.exit(1)
            
    except requests.RequestException as e:
        print(f"Error connecting to node: {str(e)}")
        sys.exit(1)


def consensus(args: argparse.Namespace) -> None:
    try:
        # Connect to local node
        response = requests.get(f"http://{args.node}/consensus")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Consensus result: {result['message']}")
            print(f"Chain length: {result.get('length') or result.get('new_length')}")
        else:
            print(f"Error running consensus: {response.json().get('error', 'Unknown error')}")
            sys.exit(1)
            
    except requests.RequestException as e:
        print(f"Error connecting to node: {str(e)}")
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Kaidos Node CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Initialize node command
    init_parser = subparsers.add_parser("init", help="Initialize a new node")
    
    # Start node command
    start_parser = subparsers.add_parser("start", help="Start a node server")
    start_parser.add_argument(
        "--host", 
        default="0.0.0.0", 
        help="Host to bind to (default: 0.0.0.0)"
    )
    start_parser.add_argument(
        "--port", 
        type=int, 
        default=5000, 
        help="Port to bind to (default: 5000)"
    )
    
    # Add peer command
    add_peer_parser = subparsers.add_parser("add-peer", help="Add a peer to the network")
    add_peer_parser.add_argument(
        "--node", 
        default="localhost:5000", 
        help="Local node address (default: localhost:5000)"
    )
    add_peer_parser.add_argument("peer", help="Peer address (host:port)")
    
    # List peers command
    list_peers_parser = subparsers.add_parser("list-peers", help="List all peers")
    list_peers_parser.add_argument(
        "--node", 
        default="localhost:5000", 
        help="Local node address (default: localhost:5000)"
    )
    
    # Mine block command
    mine_parser = subparsers.add_parser("mine", help="Mine a new block")
    mine_parser.add_argument(
        "--node", 
        default="localhost:5000", 
        help="Local node address (default: localhost:5000)"
    )
    mine_parser.add_argument(
        "address",
        help="Miner's wallet address to receive rewards"
    )
    
    # Get blocks command
    blocks_parser = subparsers.add_parser("blocks", help="Get blockchain blocks")
    blocks_parser.add_argument(
        "--node", 
        default="localhost:5000", 
        help="Local node address (default: localhost:5000)"
    )
    blocks_parser.add_argument(
        "--start", 
        type=int, 
        help="Start index (inclusive)"
    )
    blocks_parser.add_argument(
        "--end", 
        type=int, 
        help="End index (inclusive)"
    )
    
    # Get transactions command
    tx_parser = subparsers.add_parser("transactions", help="Get pending transactions")
    tx_parser.add_argument(
        "--node", 
        default="localhost:5000", 
        help="Local node address (default: localhost:5000)"
    )
    
    # Debug transaction command
    debug_parser = subparsers.add_parser("debug", help="Debug a transaction")
    debug_parser.add_argument(
        "--node", 
        default="localhost:5000", 
        help="Local node address (default: localhost:5000)"
    )
    debug_parser.add_argument("file", help="Transaction file (JSON)")
    
    # Send transaction command
    send_parser = subparsers.add_parser("send", help="Send a transaction")
    send_parser.add_argument(
        "--node", 
        default="localhost:5000", 
        help="Local node address (default: localhost:5000)"
    )
    send_parser.add_argument("file", help="Transaction file (JSON)")
    
    # Get UTXOs command
    utxos_parser = subparsers.add_parser("utxos", help="Get UTXOs for an address")
    utxos_parser.add_argument(
        "--node", 
        default="localhost:5000", 
        help="Local node address (default: localhost:5000)"
    )
    utxos_parser.add_argument("address", help="Wallet address")
    
    # Consensus command
    consensus_parser = subparsers.add_parser("consensus", help="Run consensus algorithm")
    consensus_parser.add_argument(
        "--node", 
        default="localhost:5000", 
        help="Local node address (default: localhost:5000)"
    )
    
    args = parser.parse_args()
    
    if args.command == "init":
        init_node(args)
    elif args.command == "start":
        start_node(args)
    elif args.command == "add-peer":
        add_peer(args)
    elif args.command == "list-peers":
        list_peers(args)
    elif args.command == "mine":
        mine_block(args)
    elif args.command == "blocks":
        get_blocks(args)
    elif args.command == "transactions":
        get_transactions(args)
    elif args.command == "debug":
        debug_transaction(args)
    elif args.command == "send":
        send_transaction(args)
    elif args.command == "utxos":
        get_utxos(args)
    elif args.command == "consensus":
        consensus(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

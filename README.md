# Kaidos: Python-Based Blockchain & Cryptocurrency Implementation

[![MIT License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python Versions](https://img.shields.io/badge/python-3.8%20%7C%203.9%20%7C%203.10%20%7C%203.11-blue)](https://www.python.org/)

Kaidos is a lightweight, educational blockchain and cryptocurrency implementation written in Python. It features a complete UTXO transaction model (similar to Bitcoin), proof-of-work mining, wallet management, and peer-to-peer networking capabilities. This project serves as both a learning resource for blockchain technology and a functional cryptocurrency system.

## Key Features

- **Complete UTXO System**: Implements the Unspent Transaction Output model used by Bitcoin for secure coin tracking
- **Proof-of-Work Mining**: Includes mining functionality with difficulty adjustment and block rewards
- **Halving Mechanism**: Block rewards that halve every 210,000 blocks, similar to Bitcoin's economic model
- **Transaction Fees**: Miners receive transaction fees as incentives for including transactions in blocks
- **Secure Wallet Management**: Tools to create and manage cryptographic keys and addresses
- **Multi-Signature Support**: Create addresses requiring multiple signatures for enhanced security
- **Merkle Tree Verification**: Efficient transaction verification using cryptographic Merkle trees
- **P2P Networking**: Decentralized node communication for transaction and block propagation
- **Consensus Algorithm**: Implements chain selection based on proof-of-work and chain length
- **Command-Line Interface**: Simple CLI tools for all blockchain operations

## Getting Started

```bash
# Grab the code
git clone https://github.com/jolovicdev/kaidos.git
cd kaidos

# Set up a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install it in dev mode so you can tinker
pip install -e .
```

## Playing Around

### Wallet Stuff

```bash
# Make yourself a wallet
kaidos-wallet create

# See what wallets you've got
kaidos-wallet list

# Check your balance
kaidos-wallet balance <address>

# Need a new address? No problem
kaidos-wallet address <wallet_id>

# See all your addresses
kaidos-wallet addresses <wallet_id>

# Send some coins!
kaidos-wallet tx <sender> <recipient> <amount>

# Or save the transaction for later
kaidos-wallet tx <sender> <recipient> <amount> --output transaction.json

# Check your unspent coins
kaidos-wallet utxos <address>
```

### Running Your Own Node

```bash
# Set up your node first
kaidos-node init

# Fire it up!
kaidos-node start --host <host> --port <port>

# Do some mining (and earn some coins)
kaidos-node mine <miner_address>

# Check out the blockchain
kaidos-node blocks

# Send that transaction you saved earlier
kaidos-node send transaction.json

# Sync with other nodes
kaidos-node consensus

# Got friends? Add their nodes
kaidos-node add-peer <peer_address>

# See who you're connected to
kaidos-node list-peers

# What transactions are waiting to be mined?
kaidos-node transactions

# Check specific address balances
kaidos-node utxos <address>
```

Check out [COMMANDS.md](COMMANDS.md) for all the cool things you can do.

## Sending Coins

Want to send someone some Kaidos coins? It's pretty simple:

1. Create your transaction:
   ```bash
   kaidos-wallet tx <your_address> <their_address> <amount> --output transaction.json
   ```

2. Send it to the network:
   ```bash
   kaidos-node send transaction.json
   ```

## Architecture

### Core Components

- **Blocks**: Containers for batches of transactions with cryptographic links to previous blocks
- **Blockchain**: The complete history of all blocks linked in a secure chain
- **Transaction Manager**: Handles the UTXO set, transaction validation, and mempool management
- **Wallet**: Manages cryptographic keys, addresses, and transaction signing
- **Node**: Provides network communication and consensus mechanisms

### UTXO Transaction Model

The Unspent Transaction Output (UTXO) model is a fundamental concept in Kaidos:

1. Coins exist as "unspent outputs" from previous transactions
2. When spending coins, these outputs are consumed as inputs for new transactions
3. Change from transactions is returned as a new UTXO to the sender
4. Transaction fees (the difference between inputs and outputs) are collected by miners

### Mining and Consensus

- **Block Rewards**: Miners receive 50 coins initially for each new block
- **Halving Schedule**: Rewards halve every 210,000 blocks (25, 12.5, 6.25, etc.)
- **Difficulty Adjustment**: Mining difficulty adjusts based on block generation time
- **Proof-of-Work**: Miners must find a block hash with a specific number of leading zeros
- **Chain Selection**: The longest valid chain with the most cumulative work is considered canonical

## Testing It Out

If you want to run the tests:

```bash
# Run everything
pytest

# Just test the blockchain parts
pytest Kaidos/tests/test_blockchain.py

# See all the details
pytest -v

# Check how much of the code is covered
pytest --cov=Kaidos
```

## What's Where

```
Kaidos/
├── cli/                # The command line tools
│   ├── node_cli.py     # For node commands
│   └── wallet_cli.py   # For wallet commands
├── core/               # The heart of it all
│   ├── block.py        # Block structure
│   ├── blockchain.py   # Chain management
│   ├── exceptions.py   # Custom errors
│   ├── merkle_tree.py  # Merkle tree implementation
│   └── transaction_manager.py  # Handles transactions and UTXOs
├── network/            # P2P networking
│   └── node.py         # Node implementation
├── wallet/             # Wallet functionality
│   ├── wallet.py       # Manages keys and addresses
│   └── multisig.py     # Multi-signature wallet support
└── tests/              # Making sure it all works
    ├── test_blockchain.py      # Tests for blockchain
    ├── test_consensus.py       # Tests for consensus
    ├── test_merkle_tree.py     # Tests for Merkle tree
    ├── test_multisig.py        # Tests for multi-signature
    ├── test_network.py         # Tests for networking
    ├── test_transaction_manager.py  # Tests for transactions
    └── test_wallet.py          # Tests for wallet
```

### Data Storage

Kaidos uses ZenithDB (a SQLite wrapper) for persistent storage of:

- **Blockchain Data**: All blocks and their transactions
- **UTXO Set**: The current set of unspent transaction outputs
- **Mempool**: Pending transactions waiting to be mined
- **Wallet Information**: Encrypted keys and address data
- **Network Data**: Peer connection information and node configuration

## License

This project is licensed under the MIT License - see the LICENSE file for details.

# Kaidos Cryptocurrency Commands

This document provides a comprehensive list of all available commands for the Kaidos cryptocurrency.

## Wallet Commands

```bash
# Create a new wallet
kaidos-wallet create

# Create a new encrypted wallet with passphrase protection
kaidos-wallet create --encrypted

# List all wallets
kaidos-wallet list

# Get wallet balance
kaidos-wallet balance <address>

# Create a new address for an existing wallet
kaidos-wallet address <wallet_id>

# List all addresses for a wallet
kaidos-wallet addresses <wallet_id>

# Create a transaction
kaidos-wallet tx <sender> <recipient> <amount>

# Save transaction to a file
kaidos-wallet tx <sender> <recipient> <amount> --output transaction.json

# Get UTXOs for a wallet
kaidos-wallet utxos <address>
```

## Node Commands

```bash
# Initialize a new node
kaidos-node init

# Start a node server
kaidos-node start

# Start a node server on a specific host and port
kaidos-node start --host <host> --port <port>

# Add a peer to the network
kaidos-node add-peer <peer_address>

# Add a peer to a specific node
kaidos-node add-peer --node <node_address> <peer_address>

# List all peers
kaidos-node list-peers

# List peers of a specific node
kaidos-node list-peers --node <node_address>

# Mine a new block
kaidos-node mine <miner_address>

# Mine a block on a specific node
kaidos-node mine --node <node_address> <miner_address>

# Get blockchain blocks
kaidos-node blocks

# Get blocks from a specific node
kaidos-node blocks --node <node_address>

# Get blocks in a specific range
kaidos-node blocks --start <start_index> --end <end_index>

# Get pending transactions
kaidos-node transactions

# Get transactions from a specific node
kaidos-node transactions --node <node_address>

# Send a transaction
kaidos-node send <transaction_file>

# Send a transaction to a specific node
kaidos-node send --node <node_address> <transaction_file>

# Get UTXOs for an address
kaidos-node utxos <address>

# Get UTXOs from a specific node
kaidos-node utxos --node <node_address> <address>

# Run consensus algorithm
kaidos-node consensus

# Run consensus on a specific node
kaidos-node consensus --node <node_address>
```

## Transaction Process

To send coins from one address to another, you need to follow these steps:

1. Create a transaction using the wallet CLI:
   ```bash
   kaidos-wallet tx <sender_address> <recipient_address> <amount> --output transaction.json
   ```

2. Send the transaction using the node CLI:
   ```bash
   kaidos-node send transaction.json
   ```

## Transaction File Format
When sending a transaction using the `kaidos-node send` command, you need to provide a JSON file with the following format:

```json
{
  "txid": "transaction_id",
  "inputs": [
    {
      "txid": "previous_transaction_id",
      "vout": 0,
      "signature": "input_signature"
    }
  ],
  "outputs": [
    {
      "address": "recipient_address",
      "amount": 10.0
    },
    {
      "address": "sender_address",
      "amount": 40.0
    }
  ]
}
```

The transaction file is automatically generated when you use the `kaidos-wallet tx` command with the `--output` option.

## Examples

### Creating and Using a Wallet

```bash
# Create a new wallet
kaidos-wallet create

# Check wallet balance
kaidos-wallet balance KD123456789

# Create a transaction
kaidos-wallet tx KD123456789 KD987654321 10.0 --output transaction.json

# Send the transaction
kaidos-node send transaction.json
```

### Running a Node

```bash
# Initialize a node
kaidos-node init

# Start the node
kaidos-node start --port 5000

# In another terminal, add a peer
kaidos-node add-peer localhost:5001

# Mine a block
kaidos-node mine KD123456789

# Check the blockchain
kaidos-node blocks
```

### Network Operations

```bash
# Start multiple nodes
kaidos-node start --port 5000
kaidos-node start --port 5001

# Connect nodes
kaidos-node add-peer --node localhost:5000 localhost:5001
kaidos-node add-peer --node localhost:5001 localhost:5000

# Run consensus
kaidos-node consensus

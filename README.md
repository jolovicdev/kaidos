# Kaidos Python Blockchain Cryptocurrency and wallet

Exploration of blockchain tech with a full UTXO model, mining, and all that good stuff, but still - it's a hobby project and just exploration.

## What's Inside

- A complete UTXO system (like Bitcoin uses) for tracking coins
- Mining with rewards that halve over time (just like the real thing!)
- Transaction fees for miners because they deserve something for their work
- Wallet tools to create and manage your keys securely
- P2P networking so nodes can talk to each other
- Simple command-line tools to play around with it all

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

## How It All Works

### The Building Blocks

- **Blocks** - These are batches of transactions added to the chain
- **Blockchain** - The full history of blocks linked together
- **Transaction Manager** - Keeps track of all the coins and who owns what
- **Wallet** - Your digital identity and key storage
- **Node** - Connects you to other people running Kaidos

### The UTXO Thing

1. Your coins exist as "unspent outputs" from previous transactions
2. When you spend coins, you use these outputs as inputs
3. Any leftover amount comes back to you as change
4. Miners get the difference as a fee

### Mining Rewards

- Miners start getting 50 coins per block
- Every 210,000 blocks (like Bitcoin), this cuts in half
- So eventually it goes 25, then 12.5, then 6.25... you get the idea

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
│   └── transaction_manager.py  # Handles transactions and UTXOs
├── network/            # P2P networking
│   └── node.py         # Node implementation
├── wallet/             # Wallet functionality
│   └── wallet.py       # Manages keys and addresses
└── tests/              # Making sure it all works
    └── test_*.py       # Various test files
```

### Database Stuff

I'm using ZenithDB (my sqlite3 wrapper) for data storage , It stores:

- All the blocks
- All the unspent coins (UTXOs)
- Pending transactions
- Your wallets and keys
- Connection info for other nodes

## License

This project is licensed under the MIT License - see the LICENSE file for details.

# Sending Coins with Kaidos

Hey there! This guide will walk you through sending your hard-earned Kaidos coins to other people. It's pretty straightforward once you get the hang of it!

## Before You Start

Make sure you've got:
- Kaidos up and running on your computer
- A wallet already created
- Some coins to send (from mining or someone sending you some)

### Setting Up Your Wallet

1. If you don't have a wallet yet, create one:
   ```bash
   kaidos-wallet create
   ```
   You'll get a wallet ID and your first address. Write these down!

2. Want more addresses? No problem:
   ```bash
   kaidos-wallet address <wallet_id>
   ```

3. To see all your addresses:
   ```bash
   kaidos-wallet addresses <wallet_id>
   ```

Each address is like its own separate account with its own keys, but they're all managed under one wallet.

## Step 1: Make Sure You Have Coins

First, check that you actually have coins to send:

```bash
kaidos-wallet balance <your_address>
```

Like this:
```bash
kaidos-wallet balance KDVJNZCAWP476I4JXQXRZPEBLERI7P6K5V
```

## Step 2: Create Your Transaction

Time to send some coins! Use this command:

```bash
kaidos-wallet tx <your_address> <their_address> <amount> --output transaction.json
```

For example:
```bash
kaidos-wallet tx KDVJNZCAWP476I4JXQXRZPEBLERI7P6K5V KD3P7TTS5ECJMHWA4FLL7A3OA67URTCZUK 20 --output transaction.json
```

Behind the scenes, this:
1. Finds coins in your wallet to spend
2. Creates an output sending the amount to your friend
3. Creates another output sending any leftover coins back to you
4. Signs everything with your private key
5. Saves it all to a file called transaction.json

If you set a password on your wallet, it'll ask for it now.

## Step 3: Broadcast Your Transaction

Now let's tell the network about your transaction:

```bash
kaidos-node send transaction.json
```

That's it! Your transaction is now out in the wild.

If you're running multiple nodes, you can pick which one to use:

```bash
kaidos-node send --node localhost:5000 transaction.json
```

## Step 4: Double-Check Everything Worked

Want to make sure your transaction is waiting to be mined?

```bash
kaidos-node transactions
```

Once a miner includes your transaction in a block, you can verify the coins arrived:

```bash
kaidos-wallet balance <their_address>
```

For example:
```bash
kaidos-wallet balance KD3P7TTS5ECJMHWA4FLL7A3OA67URTCZUK
```

## How it Works (The Nerdy Details)

1. **UTXOs** - These are "Unspent Transaction Outputs" - basically the coins sitting in your wallet. See yours with:
   ```bash
   kaidos-wallet utxos <your_address>
   ```

2. **Inputs** - When you send coins, you're actually spending these UTXOs and proving they're yours with your signature.

3. **Outputs** - Your transaction creates new UTXOs:
   - One for your friend (the amount you're sending)
   - One for yourself (the change from your transaction)

4. **Transaction Fee** - If your inputs total more than your outputs, the difference is a tip for miners.

5. **Getting Confirmed** - A miner needs to include your transaction in a block:
   ```bash
   kaidos-node mine <miner_address>
   ```

## A Quick Example

1. Alice has 50 coins she mined earlier
2. She wants to send 20 to her friend Bob
3. She creates a transaction that:
   - Uses her 50-coin UTXO as input
   - Creates a 20-coin output for Bob
   - Creates a 30-coin output back to herself as change
4. She signs it with her private key and broadcasts it
5. Charlie (the miner) includes her transaction in a block and gets a small fee
6. Bob now has his 20 coins, and Alice has 30 left

## Troubleshooting

Things not working? Check these common issues:

- **"Not enough coins"** - Make sure your address actually has enough funds
- **Transaction getting rejected** - You might be trying to spend coins that are already spent
- **Can't connect to the network** - Is your node running? Are you connected to other nodes?
- **Password problems** - If you encrypted your wallet, make sure you're using the right password

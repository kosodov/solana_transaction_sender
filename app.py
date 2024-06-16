from flask import Flask, render_template, request, jsonify
import base58
from solana.rpc.api import Client
from solana.transaction import Transaction
from solana.keypair import Keypair
from solana.publickey import PublicKey
from solana.system_program import TransferParams, transfer
from solana.rpc.types import TxOpts
from datetime import datetime
import os

app = Flask(__name__)

# Function to send Solana transaction
def send_solana_transaction(sender_private_key, recipient_private_key, amount):
    try:
        client = Client("https://api.mainnet-beta.solana.com")

        sender_private_key_bytes = base58.b58decode(sender_private_key)
        recipient_private_key_bytes = base58.b58decode(recipient_private_key)

        if len(sender_private_key_bytes) != 64 or len(recipient_private_key_bytes) != 64:
            raise ValueError("Invalid Phantom-compatible private key format")

        sender_keypair = Keypair.from_secret_key(sender_private_key_bytes)
        recipient_keypair = Keypair.from_secret_key(recipient_private_key_bytes)
        recipient_publickey = recipient_keypair.public_key

        # Create the transfer instruction
        transfer_instruction = transfer(
            TransferParams(
                from_pubkey=sender_keypair.public_key,
                to_pubkey=recipient_publickey,
                lamports=amount
            )
        )

        # Build the transaction
        transaction = Transaction().add(transfer_instruction)
        transaction.fee_payer = sender_keypair.public_key
        transaction.recent_blockhash = client.get_recent_blockhash()["result"]["value"]["blockhash"]

        # Sign the transaction
        transaction.sign(sender_keypair, recipient_keypair)

        # Send the transaction
        response = client.send_transaction(transaction, sender_keypair, recipient_keypair, opts=TxOpts(skip_confirmation=False))

        # Log successful transaction to file
        log_file_path = "E:/Trans_logs/logs.txt"
        if os.path.exists(log_file_path):
            with open(log_file_path, 'a') as log_file:
                log_file.write(f"From: {sender_private_key}  To: {recipient_private_key}  Time: {datetime.now()}\n")
        else:
            print(f"Error: {log_file_path} does not exist or is inaccessible.")

        # Return success response with recipient public key and transaction ID
        return {
            'success': True,
            'recipient_public_key': recipient_publickey.to_base58(),
            'transaction_id': response,
            'recipient_private_key': recipient_private_key
        }

    except Exception as e:
        error_message = str(e)
        return {
            'success': False,
            'error_message': error_message,
            'recipient_private_key': recipient_private_key
        }

# Function to read private keys from file
def read_private_keys(filename):
    with open(filename, 'r') as file:
        private_keys = [line.strip() for line in file.readlines() if line.strip()]
    return private_keys

@app.route('/send_transactions', methods=['POST'])
def send_transactions():
    try:
        sender_private_key = "YOUR_PRIVATE_KEY___SENDER"
        min_amount = 900000

        # Read recipient private keys from file
        recipient_private_keys = read_private_keys("E:/Trans.txt")

        successful_transactions = []

        for recipient_private_key in recipient_private_keys:
            response = send_solana_transaction(sender_private_key, recipient_private_key, min_amount)
            if response['success']:
                successful_transactions.append(response['recipient_private_key'])

        num_successful_transactions = len(successful_transactions)

        return render_template('transaction_result.html', success=True, recipient_public_key=response['recipient_public_key'], transaction_id=response['transaction_id'], num_successful_transactions=num_successful_transactions, successful_transactions=successful_transactions)

    except Exception as e:
        return render_template('transaction_result.html', success=False, error_message=str(e))

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)

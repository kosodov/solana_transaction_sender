from flask import Flask, render_template, request, jsonify
import base58
from solana.transaction import Transaction
from solana.rpc.api import Client
from solana.keypair import Keypair
from solana.publickey import PublicKey
from solana.system_program import TransferParams, transfer
from solana.rpc.types import TxOpts

app = Flask(__name__)

# Function to send Solana transaction via Tatum API
def send_solana_transaction(sender_private_key, recipient_public_key, amount):
    try:
        client = Client("https://api.mainnet-beta.solana.com")

        # Decode the Phantom-compatible private key
        private_key_bytes = base58.b58decode(sender_private_key)
        if len(private_key_bytes) != 64:
            raise ValueError("Invalid Phantom-compatible private key format")

        # Create sender's keypair from the private key bytes directly
        sender_keypair = Keypair.from_secret_key(private_key_bytes)

        # Prepare the transaction instruction
        recipient_publickey = PublicKey(recipient_public_key)
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
        transaction.sign(sender_keypair)

        # Send the transaction
        response = client.send_transaction(transaction, sender_keypair, opts=TxOpts(skip_confirmation=False))

        return response

    except Exception as e:
        return str(e)  # Return error message as a string

# Route for sending Solana transaction
@app.route('/send_transaction', methods=['POST'])
def send_transaction():
    try:
        # Extract data from the request
        sender_private_key = request.form['sender_private_key']
        recipient_public_key = request.form['recipient_public_key']
        amount = int(request.form['amount'])

        # Call send_solana_transaction function
        response = send_solana_transaction(sender_private_key, recipient_public_key, amount)

        return jsonify({'result': response})

    except Exception as e:
        return jsonify({'error': str(e)})

# Route for rendering the form
@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)

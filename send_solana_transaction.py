import argparse
import base58
from solana.transaction import Transaction, Keypair
from solana.rpc.api import Client

# Function to send Solana transaction via Tatum API
def send_solana_transaction(sender_private_key, recipient_public_key, amount):
    client = Client("https://api.tatum.io/v3/blockchain/node/solana-mainnet")

    # Decode the Phantom-compatible private key
    private_key_bytes = base58.b58decode(sender_private_key)
    if len(private_key_bytes) != 64:
        raise ValueError("Invalid Phantom-compatible private key format")

    # Create sender's keypair from the private key bytes directly
    sender_keypair = Keypair(bytes(private_key_bytes[:32]))  # Use first 32 bytes for secret key

    # Prepare the transaction instruction
    instruction = Transaction(
        keys=[
            AccountMeta(pubkey=sender_keypair.public_key(), is_signer=True, is_writable=True),
            AccountMeta(pubkey=recipient_public_key, is_signer=False, is_writable=True),
        ],
        program_id=client.loader_id,
        data=bytes(amount)
    )

    # Build the transaction
    transaction = Transaction(
        recent_blockhash=client.get_recent_blockhash()["result"]["value"]["blockhash"],
        instructions=[instruction],
        fee_payer=sender_keypair.public_key()
    )

    # Sign the transaction
    transaction.sign(sender_keypair)

    # Send the transaction
    response = client.send_transaction(transaction)

    return response

# Example usage
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Send Solana transaction")
    parser.add_argument("sender_private_key", type=str, help="Sender's Phantom-compatible private key")
    parser.add_argument("recipient_public_key", type=str, help="Recipient's public key")
    parser.add_argument("amount", type=int, help="Amount to send in minimal units")
    args = parser.parse_args()

    sender_private_key = args.sender_private_key
    recipient_public_key = args.recipient_public_key
    amount = args.amount

    try:
        response = send_solana_transaction(sender_private_key, recipient_public_key, amount)
        print(f"Transaction sent successfully to {recipient_public_key}. Transaction ID: {response}")
    except Exception as e:
        print(f"Failed to send transaction: {str(e)}")

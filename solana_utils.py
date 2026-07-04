from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.system_program import transfer as transfer_sol
from solders.message import MessageV0
from solders.transaction import VersionedTransaction
from solana.rpc.async_api import AsyncClient, TxOptsModel, Commitment

RPC_URL = "https://api.devnet.solana.com"


def create_wallet() -> Keypair:
    return Keypair()


def wallet_from_private_key(private_key_b58: str) -> Keypair:
    return Keypair.from_base58_string(private_key_b58)


async def get_balance(public_key_b58: str) -> float:
    async with AsyncClient(RPC_URL) as client:
        pubkey = Pubkey.from_string(public_key_b58)
        resp = await client.get_balance(pubkey, Commitment.CONFIRMED)
        return resp.value / 1_000_000_000


async def transfer_sol_to_user(sender_private_key_b58: str, recipient_pubkey_b58: str, amount_sol: float) -> str:
    sender = wallet_from_private_key(sender_private_key_b58)
    recipient = Pubkey.from_string(recipient_pubkey_b58)
    lamports = int(amount_sol * 1_000_000_000)

    async with AsyncClient(RPC_URL) as client:
        blockhash_resp = await client.get_latest_blockhash(Commitment.CONFIRMED)
        recent_blockhash = blockhash_resp.value.blockhash

        ix = transfer_sol(
            {"from_pubkey": sender.pubkey(), "to_pubkey": recipient, "lamports": lamports},
        )

        msg = MessageV0.try_compile(
            sender.pubkey(),
            [ix],
            [],
            recent_blockhash,
        )

        tx = VersionedTransaction(msg, [sender])

        opts = TxOptsModel(skip_preflight=False, preflight_commitment=Commitment.CONFIRMED)
        resp = await client.send_transaction(tx, opts)
        return str(resp.value)


async def request_airdrop(public_key_b58: str, amount_sol: float = 2.0) -> str:
    pubkey = Pubkey.from_string(public_key_b58)
    lamports = int(amount_sol * 1_000_000_000)

    async with AsyncClient(RPC_URL) as client:
        resp = await client.request_airdrop(pubkey, lamports, Commitment.CONFIRMED)
        return str(resp.value)

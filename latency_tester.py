from curses import start_color
import yaml
import time
import requests
import json
import core
from datetime import datetime
from web3 import Web3, EthereumTesterProvider
from web3.middleware import geth_poa_middleware

# This test doesn't relate to actual code but helps us a get an estimate
# of how much time passes between sending transaction and it getting confirmed 
def latency_experiment():
    # Load up config
    config = yaml.safe_load(open("config.yml"))

    # Initialize RPC endpoint
    w3 = Web3(Web3.HTTPProvider(config['rpc']))
    print(f"Welcome, web3 connection - {w3.isConnected()}")

    # We need to do this, even though Avalanche is not POA
    w3.middleware_onion.inject(geth_poa_middleware, layer=0)

    # Load up the adrdress and checksum it in case it wasn't submited properly
    contract_address = Web3.toChecksumAddress(config['address'])
    print(f'Atemptimg a mint on {contract_address}')

    # We can fetch API from snowtrace API without having to deal with it ourselves
    target_contract = w3.eth.contract(address=contract_address, abi=core.fetch_abi(contract_address))
    print(f'Contract ABI fetched, determining the start time...')

    # For the test we only need one account and one signed transaction
    key_address = json.load(open(config['production_adresses']))["data"][0]
    mint_txn = target_contract.functions.allowlistMint(config["transaction_settings"]["count"]).buildTransaction({
            'gas': config["transaction_settings"]["gas"],
            'maxFeePerGas': Web3.toWei(config["transaction_settings"]["max_fee"], 'gwei'),
            'maxPriorityFeePerGas': Web3.toWei(config["transaction_settings"]["max_priority_fee"], 'gwei'),
            'nonce': w3.eth.get_transaction_count(Web3.toChecksumAddress(key_address["address"])),
            'value' : config["transaction_settings"]["value"]
        })

    signed_transaction = w3.eth.account.sign_transaction(mint_txn, private_key=key_address["key"]).rawTransaction

    # Finally, can send a transaction and measure timings
    start_time = time.time()
    sent_tx = w3.eth.send_raw_transaction(signed_transaction).hex()
    end_time = time.time()

    print(f'Transaction hex: {sent_tx}')

    # We also need to see when transaction actually got processed by the chain
    # For that, we get block number first, it's not instantly available so we wait
    time.sleep(10)
    transaction_block = w3.eth.get_transaction(sent_tx)['blockNumber'] 

    # Next, we get block timestamp 
    block_timestamp = w3.eth.get_block(transaction_block)['timestamp']

    # With three times can output the results
    print(f'Took {end_time - start_time} seconds to send transaction')
    print(f"Transaction was confirmed {block_timestamp-start_time} seconds later")

if __name__ == '__main__':
    latency_experiment()
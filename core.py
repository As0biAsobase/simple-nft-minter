from web3 import Web3, EthereumTesterProvider
import requests
import json
from datetime import datetime
import time
import multiprocessing
import yaml

# Fetching ABI for a specified contract from a Snowtrace API
def fetch_abi(contract_address):
    url = f"https://api.snowtrace.io/api?module=contract&action=getabi&address={contract_address}"
    return requests.get(url).json()['result']

# Helper function for getting time reamining from time now
def time_until(ts):
    return ts - int(time.time())

# Addresses in keys are supplied separately in a json file
def fetch_addresses():
    return json.load(open('keys_adresses.json'))["data"]

# Sending a pre-signed transaction
def mint(signed_tx):
    try:
        sent_tx = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        print(f"Attempted mint at {datetime.utcfromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')}")
    except Exception as e:
        print("Failed misarably, what a disgrace!")
        print(e)

# Get a mint start time from the even json object
def get_start_time(event_object):
    start_time = event_object["args"]["allowlistStartTime"]
    human_time = datetime.utcfromtimestamp(start_time).strftime('%Y-%m-%d %H:%M:%S')
    print(f' Sale strat time is {start_time} or {human_time} UTC')  

    return start_time

def catch_event(filter, target_contract):
    # Loop continiously until we detect a target event 
    event_object = 0
    while True:
        for event in filter.get_all_entries():
            event_object = Web3.toJSON(event)
            
        if event_object != 0:
            print('Target event detected!')
            print(event_object)
            break
        else: 
            # Wait 2 seconds (~AVAX blocktime)
            time.sleep(2)

    return json.loads(event_object)

def sign_transactions(keys_addresses, target_contract):
    signed_transactions = []
    # Loop through all accounts and generate a mint transaction for each of them
    for pair in keys_addresses:
        # Build transaction with pre-set parameters
        if config["transaction_settings"]["is_wl"]: 
            mint_txn = target_contract.functions.allowlistMint(
                config["transaction_settings"]["count"]
            )
        else: 
            mint_txn = target_contract.functions.publicSaleMint(
                config["transaction_settings"]["count"]
            ) 
            
        
        mint_txn = mint_txn.buildTransaction({
            'gas': config["transaction_settings"]["gas"],
            'maxFeePerGas': Web3.toWei(config["transaction_settings"]["max_fee"], 'gwei'),
            'maxPriorityFeePerGas': Web3.toWei(config["transaction_settings"]["max_priority_fee"], 'gwei'),
            'nonce': w3.eth.get_transaction_count( Web3.toChecksumAddress(pair["address"])),
            'value' : config["transaction_settings"]["value"]
        })

        # Sign each transaction with private key
        signed_tx = w3.eth.account.sign_transaction(mint_txn, private_key=pair["key"])
        signed_transactions.append(signed_tx)

    return signed_transactions

def main():
    contract_address = config['address']
    print(f'Atemptimg a mint on {contract_address}')

    # We can fetch API from snowtrace API without having to deal with it ourselves
    target_contract = w3.eth.contract(address=contract_address, abi=fetch_abi(contract_address))
    print(f'Contract ABI fetched, determining the start time...')
    

    # Attempt to collect start time if initialized and fall back to waiting to initialization event if failed
    try:
        start_time = target_contract.functions.allowlistStartTime().call() #publicSaleStartTime allowlistStartTime
    except:
        print("Failed to get start time, atempting to listen for Initialization event")
        
        # Create a filter for the Initialized event
        initialized_event = target_contract.events.Initialized()
        initialized_filter = initialized_event.createFilter(fromBlock='latest')

        # Waiting and catching the Initialized() even on the target contract to derive the start time
        event_object = catch_event(initialized_filter, target_contract)
        start_time = get_start_time(event_object)

    # Calculate time left until the mint
    time_left = time_until(start_time)
    print(f'{time_left} seconds left')

    # Getting the 3 accounts that we'll use for minting
    keys_addresses = fetch_addresses()
    print(f'Got {len(keys_addresses)} wallets, building the transactions array...')

    # We generate and sign all transactions in advance, so the only thing left is to send them
    signed_transactions = sign_transactions(keys_addresses, target_contract)
    print("Transactions prepered, starting the wait...")

    # Simply waiting for the mint to start
    while time.time() < start_time:
        time.sleep(0.001)
        
    print('Time is now, attempting mint')
    
    # Run minting on multiple accounts in parallel
    # This part doesn't work on Windows because it uses Spawn instead of Fork
    process_count = multiprocessing.cpu_count()
    print(f"Running minting on {process_count} threads")
    pool = multiprocessing.Pool(processes=process_count)

    pool.map(mint, signed_transactions)
    pool.close()


if __name__ == "__main__":
    global w3, config

    # Load up config
    config = yaml.safe_load(open("config.yml"))

    # Initialize RPC endpoint
    w3 = Web3(Web3.HTTPProvider(config['rpc']))
    print(f"Welcome, web3 connection - {w3.isConnected()}")

    main()
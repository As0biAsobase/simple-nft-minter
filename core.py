from web3 import Web3, EthereumTesterProvider
import requests
import json
from datetime import datetime
import time
import multiprocessing

def fetch_abi(contract_address):
    url = f"https://api.snowtrace.io/api?module=contract&action=getabi&address={contract_address}"
    return requests.get(url).json()['result']

def time_until(ts):
    return ts - int(time.time())

def fetch_addresses():
    return json.load(open('keys_adresses.json'))["data"]

def gas_estimate(w3, multiplier):
    return int(w3.eth.gas_price / 10**9) * multiplier

def mint(signed_tx):
    try:
        sent_tx = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        print(f"Attempted mint at {datetime.utcfromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')}")
    except Exception as e:
        print(e)

def test(contract, key, address):
    print(contract, key, address)


def main():
    contract_address = '0x3DD5e0f0659cA8b52925E504FE9f0250bFe68301'
    print(f'Atemptimg a mint on {contract_address}')

    target_contract = w3.eth.contract(address=contract_address, abi=fetch_abi(contract_address))
    print(f'Contract ABI fetched, determining the start time...')
    
    event_filter = target_contract.events.Initialized.createFilter(fromBlock='latest')
    start_time = 0
    while True:
        for Initialized in event_filter:
            event_object = Web3.toJSON(Initialized)
            start_time = event_object["Args"]["allowlistStartTime"]
        if start_time > 0:
            human_time = datetime.utcfromtimestamp(start_time).strftime('%Y-%m-%d %H:%M:%S')
            print(f'Initialized() event caught. Sale strat time is {start_time} or {human_time} UTC')  
            break
        else: 
            time.sleep(0.2)

    time_left = time_until(start_time)
    print(f'{time_left} seconds left')

    keys_addresses = fetch_addresses()
    print(f'Got {len(keys_addresses)} wallets, building the transactions array...')

    signed_transactions = []
    for pair in keys_addresses:
        mint_txn = target_contract.functions.publicSaleMint(
            1
        ).buildTransaction({
            # 'value' : 2*10**18,
            'gas': 300000,
            'maxFeePerGas': Web3.toWei('300', 'gwei'),
            'maxPriorityFeePerGas': Web3.toWei('50', 'gwei'),
            'nonce': w3.eth.get_transaction_count( Web3.toChecksumAddress(pair["address"])),
        })

        signed_tx = w3.eth.account.sign_transaction(mint_txn, private_key=pair["key"])
        signed_transactions.append(signed_tx)

    while time.time() < start_time:
        time.sleep(0.001)
        
    print('Time is now, attempting mint')
    
    process_count = multiprocessing.cpu_count()
    print(f"Running minting on {process_count} threads")
    pool = multiprocessing.Pool(processes=process_count)

    pool.map(mint, signed_transactions)
    pool.close()


if __name__ == "__main__":
    global w3 
    w3 = Web3(Web3.HTTPProvider('https://api.avax.network/ext/bc/C/rpc'))
    print(f"Welcome, web3 connection - {w3.isConnected()}")

    main()
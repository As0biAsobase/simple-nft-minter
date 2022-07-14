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
    except Exception as e:
        print(e)

def test(contract, key, address):
    print(contract, key, address)

def main():
    contract_address = '0xA870fd655F40583B6c33Ed13363DEffF7958a8D0'
    print(f'Atemptimg a mint on {contract_address}')

    target_contract = w3.eth.contract(address=contract_address, abi=fetch_abi(contract_address))
    sale_start_time = target_contract.functions.publicSaleStartTime().call()
    human_time = datetime.utcfromtimestamp(sale_start_time).strftime('%Y-%m-%d %H:%M:%S')
    print(f'Contract ABI fetched, sale strat time is {sale_start_time} or {human_time} UTC')

    time_left = time_until(sale_start_time)
    print(f'{time_left} seconds left')

    keys_addresses = fetch_addresses()
    print(f'Got {len(keys_addresses)} wallets, building the transactions array...')

    signed_transactions = []
    for pair in keys_addresses:
        mint_txn = target_contract.functions.publicSaleMint(
            1
        ).buildTransaction({
            'gas': 152883,
            'maxFeePerGas': Web3.toWei('100', 'gwei'),
            'maxPriorityFeePerGas': Web3.toWei('40', 'gwei'),
            'nonce': w3.eth.get_transaction_count( Web3.toChecksumAddress(pair["address"])),
        })

        signed_tx = w3.eth.account.sign_transaction(mint_txn, private_key=pair["key"])
        signed_transactions.append(signed_tx)

    while time.time() < sale_start_time:
        time.sleep(0.05)
        
    print('Time is now, attempting mint')
    
    process_count = multiprocessing.cpu_count()
    print(f"Running minting on {process_count} threads")
    pool = multiprocessing.Pool(processes=process_count)

    pool.map(mint, signed_transactions)
    pool.close()
    # for pair in keys_addresses:
    #     mint(w3, target_contract, pair['key'], Web3.toChecksumAddress(pair['address']))




if __name__ == "__main__":
    global w3 
    w3 = Web3(Web3.HTTPProvider('https://api.avax.network/ext/bc/C/rpc'))
    print(f"Welcome, web3 connection - {w3.isConnected()}")

    main()
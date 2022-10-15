import pytest 
import core 
from web3 import Web3, EthereumTesterProvider

# Testing with the wolfi contract
@pytest.fixture(scope="session", autouse=True)
def setup_and_teardown():
    global w3, contract_address, target_contract 

    w3 = Web3(Web3.HTTPProvider('https://api.avax.network/ext/bc/C/rpc'))
    contract_address = '0xBC3323468319CF1a2a9CA71A6f4034b7Cb5F8126'
    target_contract = w3.eth.contract(address=contract_address, abi=core.fetch_abi(contract_address))

    yield

def test_abi_fetching():
    core.fetch_abi('0xBC3323468319CF1a2a9CA71A6f4034b7Cb5F8126')

# Checking if we would have caught the initilization of Wolfi
def test_event_catcher():
    initialized_event = target_contract.events.Initialized()
    initialized_filter = initialized_event.createFilter(fromBlock=20968390, toBlock=20970438)
    
    object = core.catch_event(initialized_filter, target_contract)
    assert len(object) != 0
        
# Checking if our approach actually catches initialization and not some rubbish
def test_event_catcher_fails():
    initialized_event = target_contract.events.Initialized()
    initialized_filter = initialized_event.createFilter(fromBlock=20968300, toBlock=20968380)
    
    object = initialized_filter.get_all_entries()
    assert len(object) == 0

# Test if we are able to calculate start time from event object
def test_start_time_getter():
    event_object = {
        "args": {
            "allowlistStartTime": 1665680400,
            "publicSaleStartTime": 1665681000,
            }, 
            "event": "Initialized"
    }

    start_time = core.get_start_time(event_object)
    assert start_time == 1665680400


# Test if we are able to calculate start time from the actual real-life event object 
# WARNING: This will fail if test_event_catcher() fails
def test_start_time_chained():
    initialized_event = target_contract.events.Initialized()
    initialized_filter = initialized_event.createFilter(fromBlock=20968390, toBlock=20970438)
    
    event_object = core.catch_event(initialized_filter, target_contract)
    start_time = core.get_start_time(event_object)

    assert start_time == 1665680400
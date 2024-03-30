import logging
import requests
import pprint


logger = logging.getLogger() # Binance connector


def get_contracts():
    response_object = requests.get("https://fapi.binance.com/fapi/v1/exchangeInfo") #base endpoint
    contracts = []
    
    for contract in response_object.json()['symbols']: 
        contracts.append(contract['pair'])
    
    return contracts

    #pprint.pprint(response_object.json()['symbols'])

print(get_contracts())






# rest apis are used to: place order, cancel order, get current balance of account
# base urls:
# "https://fapi.binance.com"
# "https://testnet.binancefuture.com"

# web socket used to get live market data
# "wss://fstream.binance.com" has continuous connection, no need to periodically send requests like REST apis
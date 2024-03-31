import logging
import requests


logger = logging.getLogger() # Binance connector


class BinanaceFuturesClient:
    def __init__(self, testnet):
        if testnet:
            self.base_url = "https://testnet.binancefuture.com"
        else:
            self.base_url = "https://fapi.binance.com"
        
        logger.info("Binance Futures Client successfully initialized")

        self.prices = {} #dict with contract name as key with price as a value



    def make_request(self, method, endpoint, data): #http method, endpoint, parameters
        if method == "GET": #http method
            response = requests.get(self.base_url + endpoint, params=data) #returns the response object 
        else:
            raise ValueError()
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.error("Error while making %s request to %s: %s (error code %s)",     
                                method, endpoint, response.json(), response.status_code) # %s gets replaced by the arguments
            return None #if we get an error, we can't use the output of make_requests

    def get_contracts(self):
        exchange_info = self.make_request("GET", "/fapi/v1/exchangeInfo", None)

        contracts = {}

        if exchange_info is not None:
            for contract_data in exchange_info['symbols']:
                contracts[contract_data['pair']] = contract_data

        return contracts
    
    def get_historical_candles(self, symbol, interval):
        data = {}
        data['symbol'] = symbol
        data['interval'] = interval
        data['limit'] = 1000

        raw_candles = self.make_request("GET", "/fapi/v1/klines", data)
        candles = []

        if raw_candles is not None: #if request was successful
            for c in raw_candles:
                candles.append([c[0], float(c[1]), float(c[2]), float(c[3]), float(c[4]), float(c[5])]) #c1 = open price, c2 = high price, c3 = low price, c4 = close price, c5 = volume

        return candles
    
    def get_bid_ask(self, symbol):
        data = {}
        data['symbol'] = symbol
        ob_data = self.make_request("GET", "/fapi/v1/ticker/bookTicker", data) #"https://testnet.binancefuture.com/fapi/v1/ticker/bookTicker?symbol=BTCUSDT" #to add, &key=value&key2=value2
        
        if ob_data is not None: #if request was successful
            #update prices dictionary. symbol : bid/ask
            if symbol not in self.prices:
                self.prices[symbol] = {'bid': float(ob_data['bidPrice']), 'ask': float(ob_data['askPrice'])}
            else:
                self.prices[symbol]['bid'] = float(ob_data['bidPrice'])
                self.prices[symbol]['ask'] = float(ob_data['askPrice'])
                
        return self.prices[symbol] #return data for symbol we specified
    




# import pprint
# def get_contracts():
#     response_object = requests.get("https://fapi.binance.com/fapi/v1/exchangeInfo") #base endpoint
#     contracts = []
#     for contract in response_object.json()['symbols']: 
#         contracts.append(contract['pair'])
#     return contracts
#     #pprint.pprint(response_object.json()['symbols'])
# print(get_contracts())






# rest apis are used to: place order, cancel order, get current balance of account
# base urls:
# "https://fapi.binance.com"
# "https://testnet.binancefuture.com"

# web socket used to get live market data
# "wss://fstream.binance.com" has continuous connection, no need to periodically send requests like REST apis
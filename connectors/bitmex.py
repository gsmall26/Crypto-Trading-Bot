import logging
import requests
import time
import typing

from urllib.parse import urlencode

import hmac
import hashlib

import websocket
import json

import threading

from models import *

logger = logging.getLogger()

class BitmexClient:
    def __init__(self, public_key: str, secret_key: str, testnet: bool):
        if testnet:
            self._base_url = "https://testnet.bitmex.com"
            self._wss_url = "wss://testnet.bitmex.com/realtime"
        else:
            self._base_url = "https://www.bitmex.com"
            self._wss_url = "wss://www.bitmex.com/realtime"
        
        self._public_key = public_key
        self._secret_key = secret_key

        self._ws = None #websocket app object

        self.contracts = self.get_contracts()
        self.balances = self.get_balances()

        self.prices = {}

        # t = threading.Thread(target=self._start_ws)
        # t.start()

        logger.info("Bitmex Client successfully initialized")
    
    def _generate_signature(self, method: str, endpoint: str, expires: str, data: typing.Dict) -> str:
 
        message = method + endpoint + "?" + urlencode(data) + expires if len(data) > 0 else method + endpoint + expires
        return hmac.new(self._secret_key.encode(), message.encode(), hashlib.sha256).hexdigest()

    def _make_request(self, method: str, endpoint: str, data: typing.Dict): #http method, endpoint, parameters

        headers = {}
        expires = str(int(time.time()) + 5)
        headers['api-expires'] = expires
        headers['api-key'] = self._public_key
        headers['api-signatures'] = self._generate_signature(method, endpoint, expires, data)

        if method == "GET": #http method
            try:
                response = requests.get(self._base_url + endpoint, params=data, headers=headers) #returns the response object 
            except Exception as e:
                logger.error("Connection error while making %s request to %s: %s", method, endpoint, e)
                return None

        elif method == "POST":
            try:
                response = requests.post(self._base_url + endpoint, params=data, headers=headers) #returns the response object         
            except Exception as e:
                logger.error("Connection error while making %s request to %s: %s", method, endpoint, e)
                return None

        elif method == "DELETE":
            try:
                response = requests.delete(self._base_url + endpoint, params=data, headers=headers) #returns the response object 
            except Exception as e:
                logger.error("Connection error while making %s request to %s: %s", method, endpoint, e)
                return None
        else:
            raise ValueError()
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.error("Error while making %s request to %s: %s (error code %s)",     
                                method, endpoint, response.json(), response.status_code) # %s gets replaced by the arguments
            return None #if we get an error, we can't use the output of make_requests

    def get_contracts(self) -> typing.Dict[str, Contract]:

        instruments = self._make_request("GET", "/api/v1/instrument/active", {})

        contracts = {}

        if instruments is not None:
            for s in instruments:
                contracts[s['symbol']] = Contract(s, "bitmex")
        
        return contracts
    
    def get_balances(self) -> typing.Dict[str, Balance]:
        data = {}
        data['currency'] = "all"

        margin_data = self._make_request("GET", "/api/v1/user/margin", data)

        balances = {}
        
        if margin_data is not None:
            for a in margin_data:
                balances[a['currency']] = Balance(a, "bitmex")
        
        return balances

    def get_historical_chandles(self, contract: Contract, timeframe: str) -> typing.Dict[Candle]:
        data = {}

        data['symbol'] = contract.symbol
        data['partial'] = True
        data['binSize'] = timeframe
        data['count'] = 500

        raw_candles = self._make_request("GET", "api/v1/trade/bucketed", data)

        candles = []

        if raw_candles is not None:
            for c in raw_candles:
                candles.append(Candle(c, "bitmex"))

        return candles

    
    def place_order(self, contract: Contract, order_type: str, quantity: int, side: str, price=None, tif=None) -> OrderStatus:
        data = {}

        data['symbol'] = contract.symbol
        data['side'] = side.capitalize() # must be "Buy" or "Sell"
        data['orderQty'] = quantity
        data['ordType'] = order_type.capitalize()

        if price is not None:
            data['price'] = price

        if tif is not None:
            data['timeInForce'] = tif

        order_status = self._make_request("POST", "/api/v1/order", data)

        if order_status is not None:
            order_status = OrderStatus(order_status, "bitmex")
        
        return order_status

    def cancel_order(self, order_id: str):
        data = {}
        data['orderID'] = order_id

        order_status = self._make_request("DELETE", "/api/v1/order", data) #returns list of dictionaries

        if order_status is not None:
            order_status = OrderStatus(order_status[0], "bitmex") #cancel orders one by one
        
        return order_status

    def get_order_status(self, order_id: str, contract: Contract):   
        data = {}
        data['symbol'] = contract.symbol
        data['reverse'] = True #first elements in the list will be the newest order IDs

        order_status = self._make_request("GET", "/api/v1/order", data) 

        if order_status is not None:
            for order in order_status: #list of order dictionaries relating to the symbol we requested. look for specific order id
                if order['orderID'] == order_id: #we found the orderID that we are interested in
                    return OrderStatus(order, "bitmex") 
        
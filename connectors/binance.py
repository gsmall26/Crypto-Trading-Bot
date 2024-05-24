import logging
import requests
import time
import typing # in order to type more complex variables, strings, floating numbers, etc. ex: specifying an argument needs to be passed as a dict: typing.Dict
import collections

from urllib.parse import urlencode
import hmac
import hashlib

import websocket
import json

import threading #used to create threads. goal is to run function in parallel so we don't get stuck in our loop

from models import *

from strategies import TechnicalStrategy, BreakoutStrategy

logger = logging.getLogger() # Binance connector


class BinanceClient:
    def __init__(self, public_key: str, secret_key: str, testnet: bool, futures: bool): #specifying the data type of arguments
        
        self.futures = futures

        if self.futures:
            self.platform = "binance_futures"
            if testnet:
                self._base_url = "https://testnet.binancefuture.com"
                self._wss_url = "wss://stream.binancefuture.com/ws" #testnet environment
                #need base url for websocket server: 2 urls, one for testnet environment and one for live environment
            else:
                self._base_url = "https://fapi.binance.com"
                self._wss_url = "wss://fstream.binance.com/ws" #live environment
        else:
            self.platform = "binance_spot"
            if testnet:
                self._base_url = "https://testnet.binance.vision"
                self._wss_url = "wss://testnet.binance.vision/ws"

            else:
                self._base_url = "https://api.binance.com"
                self._wss_url = "wss://stream.binance.com:9443/ws" 
            
        self._public_key = public_key
        self._secret_key = secret_key

        self._headers = {'X-MBX-APIKEY': self._public_key}

        self.contracts = self.get_contracts()
        self.balances = self.get_balances()

        self.prices = {} #dict with contract name as key with price as a value
        self.strategies: typing.Dict[int, typing.Union[TechnicalStrategy, BreakoutStrategy]] = {}

        self.logs = []

        self._ws_id = 1 #increment any time we call subscribe channel method
        self.ws: websocket.WebSocketApp
        self.reconnect = True
        self.ws_connected = False
        self.ws_subscriptions = {"bookTicker": [], "aggTrade": []}

        t = threading.Thread(target=self._start_ws) #creating thread object
        t.start() #start

        logger.info("Binance Futures Client successfully initialized")

    
    def _add_log(self, msg: str):
        logger.info("%s", msg)
        self.logs.append({"log": msg, "displayed": False})

    def _generate_signature(self, data: typing.Dict) -> str: #_private_method()
        return hmac.new(self._secret_key.encode(), urlencode(data).encode(), hashlib.sha256).hexdigest() #convert string to byte object with encode(), convert data to query string


    def _make_request(self, method: str, endpoint: str, data: typing.Dict): #http method, endpoint, parameters
        if method == "GET": #http method
            try:
                response = requests.get(self._base_url + endpoint, params=data, headers=self._headers) #returns the response object 
            except Exception as e:
                logger.error("Connection error while making %s request to %s: %s", method, endpoint, e)
                return None

        elif method == "POST":
            try:
                response = requests.post(self._base_url + endpoint, params=data, headers=self._headers) #returns the response object         
            except Exception as e:
                logger.error("Connection error while making %s request to %s: %s", method, endpoint, e)
                return None

        elif method == "DELETE":
            try:
                response = requests.delete(self._base_url + endpoint, params=data, headers=self._headers) #returns the response object 
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


    def get_contracts(self) -> typing.Dict[str, Contract]: #returns a dictionary with strings as keys and Contract objects as values
        
        if self.futures:
            exchange_info = self._make_request("GET", "/fapi/v1/exchangeInfo", {})
        else:
            exchange_info = self._make_request("GET", "/api/v3/exchangeInfo", {})

        contracts = {}

        if exchange_info is not None:
            for contract_data in exchange_info['symbols']:
                contracts[contract_data['symbol']] = Contract(contract_data, self.platform)
        
        return collections.OrderedDict(sorted(contracts.items()))  #sorts keys of the dictionary alphabetically

    
    def get_historical_candles(self, contract: Contract, interval: str) -> typing.List[Candle]: #specifies our output is a list of Candle objects
        data = {}
        data['symbol'] = contract.symbol
        data['interval'] = interval
        data['limit'] = 1000

        if self.futures:
            raw_candles = self._make_request("GET", "/fapi/v1/klines", data)
        else:
            raw_candles = self._make_request("GET", "/api/v3/klines", data)

        candles = []

        if raw_candles is not None: #if request was successful
            for c in raw_candles:
                candles.append(Candle(c, interval, self.platform)) #create Candle object and provide it with information --> c1 = open price, c2 = high price, c3 = low price, c4 = close price, c5 = volume
        
        return candles #return list of Candle objects
    

    def get_bid_ask(self, contract: Contract) -> typing.Dict[str, float]:
        data = {}
        data['symbol'] = contract.symbol

        if self.futures:
            ob_data = self._make_request("GET", "/fapi/v1/ticker/bookTicker", data) #"https://testnet.binancefuture.com/fapi/v1/ticker/bookTicker?symbol=BTCUSDT" #to add, &key=value&key2=value2
        else:
            ob_data = self._make_request("GET", "/api/v3/ticker/bookTicker", data)
        
        if ob_data is not None: #if request was successful
            #update prices dictionary. symbol : bid/ask
            if contract.symbol not in self.prices:
                self.prices[contract.symbol] = {'bid': float(ob_data['bidPrice']), 'ask': float(ob_data['askPrice'])}
            else:
                self.prices[contract.symbol]['bid'] = float(ob_data['bidPrice'])
                self.prices[contract.symbol]['ask'] = float(ob_data['askPrice'])
                
            return self.prices[contract.symbol] #return data for symbol we specified
    

    def get_balances(self) -> typing.Dict[str, Balance]:
        data = {}
        data['timestamp'] = int(time.time() * 1000)
        data['signature'] = self._generate_signature(data)

        balances = {} #key will be asset name, value will be information about asset

        if self.futures:
            account_data = self._make_request("GET", "/fapi/v1/account", data)
        else:
            account_data = self._make_request("GET", "/api/v3/account", data)

        if account_data is not None: #if request was successful
            if self.futures:
                for a in account_data['assets']: #loop through information in assets list
                    balances[a['asset']] = Balance(a, self.platform)
            else:
                for a in account_data['balances']:
                    balances[a['asset']] = Balance(a, self.platform)

        return balances
    

    def place_order(self, contract: Contract, order_type: str, quantity: float, side: str, price=None, tif=None) -> OrderStatus:
        data = {} #dictionary of parameters
        data['symbol'] = contract.symbol
        data['side'] = side.upper()
        data['quantity'] = round(int(quantity / contract.lot_size) * contract.lot_size, 8)
        data['type'] = order_type.upper()

        if price is not None: # if we get a price argument
            data['price'] = round(round(price / contract.tick_size) * contract.tick_size, 8) # add price to dictionary of parameters
            data['price'] = '%.*f' % (contract.price_decimals, data['price'])  # Avoids scientific notation

        if tif is not None: # same for time in force
            data['timeInForce'] = tif
        
        data['timestamp'] = int(time.time() * 1000)
        data['signature'] = self._generate_signature(data)

        if self.futures:
            order_status = self._make_request("POST", "/fapi/v1/order", data)
        else:
            order_status = self._make_request("POST", "/api/v3/order", data)

        if order_status is not None:

            if not self.futures:
                if order_status['status'] == "FILLED":
                    order_status['avgPrice'] = self._get_execution_price(contract, order_status['orderId'])
                else:
                    order_status['avgPrice'] = 0

            order_status = OrderStatus(order_status, self.platform)

        return order_status
    

    def cancel_order(self, contract: Contract, order_id: int) -> OrderStatus:
        data = {}
        data['orderId'] = order_id
        data['symbol'] = contract.symbol

        data['timestamp'] = int(time.time() * 1000)
        data['signature'] = self._generate_signature(data)

        if self.futures:
            order_status = self._make_request("DELETE", "/fapi/v1/order", data)
        else:
            order_status = self._make_request("DELETE", "/api/v3/order", data)

        if order_status is not None:
            if not self.futures:
                order_status['avgPrice'] = self._get_execution_price(contract, order_id)
            order_status = OrderStatus(order_status, self.platform)

        return order_status

    def _get_execution_price(self, contract: Contract, order_id: int) -> float:

        data = {}
        data['timestamp'] = int(time.time() * 1000)
        data['symbol'] = contract.symbol
        data['signature'] = self._generate_signature(data)

        trades = self._make_request("GET", "/api/v3/myTrades", data)

        avg_price = 0

        if trades is not None:

            executed_qty = 0
            for t in trades:
                if t['orderId'] == order_id:
                    executed_qty += float(t['qty'])

            for t in trades:
                if t['orderId'] == order_id:
                    fill_pct = float(t['qty']) / executed_qty
                    avg_price += (float(t['price']) * fill_pct)

        return round(round(avg_price / contract.tick_size) * contract.tick_size, 8)

    def get_order_status(self, contract: Contract, order_id: int) -> OrderStatus:

        data = {}
        data['timestamp'] = int(time.time() * 1000)
        data['symbol'] = contract.symbol
        data['orderId'] = order_id
        data['signature'] = self._generate_signature(data)

        if self.futures:
            order_status = self._make_request("GET", "/fapi/v1/order", data)
        else:
            order_status = self._make_request("GET", "/api/v3/order", data)

        if order_status is not None:
            if not self.futures:
                if order_status['status'] == "FILLED":
                    order_status['avgPrice'] = self._get_execution_price(contract, order_id)
                else:
                    order_status['avgPrice'] = 0

            order_status = OrderStatus(order_status, self.platform)

        return order_status
    

    def _start_ws(self): #starts connection and assign a certain function when an event occurs
        self.ws = websocket.WebSocketApp(self._wss_url, on_open=self._on_open, on_close=self._on_close, on_error=self._on_error, #websocketApp object. first argument is websocket url, others to specify call back
                                    on_message=self._on_message)
        while True:
            try:
                if self.reconnect:
                    self.ws.run_forever() #infinite loop waiting for messages from server. when message is received, callback function can be triggered
                else:
                    break
            except Exception as e:
                logger.error("Binance error in run_forever() method: %s", e)
            time.sleep(2) #2 second pause

    def _on_open(self, ws):
        logger.info("Binanace connection opened") #welcome to show websocket connection has been established
        # self.subscribe_channel(list(self.contracts.values()), "bookTicker") #when connection opens, subscribe to channel
        # self.subscribe_channel(list(self.contracts.values()), "aggTrade")

        self.ws_connected = True

        # The aggTrade channel is subscribed to in the _switch_strategy() method of strategy_component.py

        for channel in ["bookTicker", "aggTrade"]:
            for symbol in self.ws_subscriptions[channel]:
                self.subscribe_channel([self.contracts[symbol]], channel, reconnection=True)

        if "BTCUSDT" not in self.ws_subscriptions["bookTicker"]:
            self.subscribe_channel([self.contracts["BTCUSDT"]], "bookTicker")


    def _on_close(self, ws, close_status_code, close_msg):
        logger.warning("Binance Websocket connection closed")
        self.ws_connected = False
    
    def _on_error(self, ws, msg: str):
        logger.error("Binanace connection error: %s", msg)

    def _on_message(self, ws, msg: str):
        data = json.loads(msg) #convert json string that we received to json object that we can pass. loads() does this
        
        if "u" in data and "A" in data:
            data['e'] = "bookTicker"

        if "e" in data:
            if data['e'] == "bookTicker":

                symbol = data['s']

                if symbol not in self.prices:
                    self.prices[symbol] = {'bid': float(data['b']), 'ask': float(data['a'])}
                else:
                    self.prices[symbol]['bid'] = float(data['b'])
                    self.prices[symbol]['ask'] = float(data['a'])
                
                #pnl calculations/updates
                try:
                    for b_index, strat in self.strategies.items():
                        if strat.contract.symbol == symbol:
                            for trade in strat.trades:
                                if trade.status == "open" and trade.entry_price is not None:
                                    if trade.side == "long":
                                        trade.pnl = (self.prices[symbol]['bid'] - trade.entry_price) * trade.quantity
                                    elif trade.side == "short":
                                        trade.pnl = (trade.entry_price - self.prices[symbol]['bid']) * trade.quantity
                except RuntimeError as e:
                    logger.error("Error while looping through the Binance strategies: %s", e)

            if data['e'] == "aggTrade":
                symbol = data['s']

                for key, strat in self.strategies.items():
                    if strat.contract.symbol == symbol:
                        res = strat.parse_trades(float(data['p']), float(data['q']), data['T'])
                        strat.check_trade(res)
        
    
    def subscribe_channel(self, contracts: typing.List[Contract], channel: str, reconnection=False): #subscribe to a channel that provides us with market data. parameter is symbol you want data on
        #creating json object. create python dict and fill it with the keys from binance documentation

        if len(contracts) > 200:
            logger.warning("Subscribing to more than 200 symbols will most likely fail. "
                           "Consider subscribing only when adding a symbol to your Watchlist or when starting a strategy for a symbol.")

        data = {}
        data['method'] = "SUBSCRIBE"
        data['params'] = [] #list of channels we want to subscribe to

        if len(contracts) == 0:
            data['params'].append(channel)
        else:
            for contract in contracts:
                if contract.symbol not in self.ws_subscriptions[channel] or reconnection:
                    data['params'].append(contract.symbol.lower() + "@" + channel) #appending to the list of channels
                    if contract.symbol not in self.ws_subscriptions[channel]:
                        self.ws_subscriptions[channel].append(contract.symbol)

            if len(data['params']) == 0:
                return

        data['id'] = self._ws_id

        #send() expects string not dict. json.dumps(data) converts dict to JSON string. similar to query string idea
        try:
            self.ws.send(json.dumps(data)) #send() to send JSON object through the websocket connection
            logger.info("Binance: subscribing to: %s", ','.join(data['params']))
        except Exception as e:
            logger.error("Websocket error while subscribing to @bookTicker and @aggTrade: %s", e)
            
        self._ws_id += 1
    
    def get_trade_size(self, contract: Contract, price: float, balance_pct: float):

        logger.info("Getting Binance trade size...")

        balance = self.get_balances()
        if balance is not None:
            if contract.quote_asset in balance:  #with binance Spot, the quote asset isn't necessarily USDT
                if self.futures:
                    balance = balance[contract.quote_asset].wallet_balance
                else:
                    balance = balance[contract.quote_asset].free
            else:
                return None
        else:
            return None
        
        trade_size = (balance * balance_pct / 100) / price

        trade_size = round(round(trade_size / contract.lot_size) * contract.lot_size, 8)

        logger.info("Binance current %s balance = %s, trade size = %s", contract.quote_asset, balance, trade_size)

        return trade_size








# rest apis are used to: place order, cancel order, get current balance of account
# base urls:
# "https://fapi.binance.com"
# "https://testnet.binancefuture.com"

# web socket used to get live market data
# "wss://fstream.binance.com" has continuous connection, no need to periodically send requests like REST apis
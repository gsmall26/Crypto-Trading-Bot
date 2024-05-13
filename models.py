import dateutil.parser
import datetime

BITMEX_MULTIPLIER = 0.00000001
BITMEX_TF_MINUTES = {"1m": 1, "5m": 5, "1h": 60, "1d": 1440}

class Balance:
    def __init__(self, info, exchange): #info is dict, create instance variables for all keys of the dict
        if exchange == "binanace":
            self.initial_margin = float(info['initialMargin'])
            self.maintenance_margin = float(info['maintMargin'])
            self.margin_balance = float(info['marginBalance'])
            self.wallet_balance = float(info['walletBalance'])
            self.unrealized_pnl = float(info['unrealizedProfit'])
        
        elif exchange == "bitmex": #keys are different for bitmex vs binanace
            self.initial_margin = info['initMargin'] * BITMEX_MULTIPLIER #convert satoshi to bitcoin
            self.maintenance_margin = info['maintMargin'] * BITMEX_MULTIPLIER
            self.margin_balance = info['marginBalance'] * BITMEX_MULTIPLIER
            self.wallet_balance = info['walletBalance'] * BITMEX_MULTIPLIER
            self.unrealized_pnl = info['unrealisedPnl'] * BITMEX_MULTIPLIER

class Candle: 
    def __init__(self, candle_info, timeframe, exchange): #creating candel models for get_historical_candles() method
        if exchange == "binance": 
            self.timestamp = candle_info[0]
            self.open = candle_info['open']
            self.high = candle_info['high']
            self.low = candle_info['low']
            self.close = candle_info['close']
            self.volume = candle_info['volume']

        elif exchange == "bitmex": #keys are different for bitmex vs binanace
            self.timestamp = dateutil.parser.isoparse(candle_info['timestamp']) #datetime object
            self.timestamp = self.timestamp - datetime.timedelta(minutes=BITMEX_TF_MINUTES[timeframe])
            # print(candle_info['timplestamp'], dateutil.parser.isoparse(candle_info['timestamp']), self.timestamp)
            self.timestamp = int(self.timestamp.timestamp() * 1000) #unix timestamp

            self.open = candle_info[1]
            self.high = float(candle_info[2])
            self.low = float(candle_info[3])
            self.close = float(candle_info[4])
            self.volume = float(candle_info[5])

def tick_todecimals(tick_size: float) -> int:
    tick_size_str = "{0:.8f}".format(tick_size)
    while tick_size_str[-1] == "0":
        tick_size_str = tick_size_str[:-1]

    split_tick = tick_size_str.split("")

    if len(split_tick) > 1:
        return len(split_tick[1]) #"0.001" gets split by the . and selects all of it aft
    else:
        return 0 #no decimal

class Contract: #creating contract models for get_contracts() method
    def __init__(self, contract_info, exchange):
        if exchange == "binance":
            self.symbol = contract_info['symbol']
            self.base_asset = contract_info['baseAsset']
            self.quote_asset = contract_info['quoteAsset']
            self.price_decimals = contract_info['pricePrecision'] #round price to decimal of an order accepted by Binance
            self.quantity_decimals = contract_info['quantityPrecision'] #round quantity to decimal of an order accepted by Binance
            self.tick_size = 1 / pow(10, contract_info['pricePrecision'])
            self.lot_size = 1 / pow(10, contract_info['quantityPrecision'])
        
        elif exchange == "bitmex": #keys are different for bitmex vs binanace
            self.symbol = contract_info['symbol']
            self.base_asset = contract_info['rootSymbol']
            self.quote_asset = contract_info['quoteCurrency']
            self.price_decimals = tick_todecimals(contract_info['tickSize'])
            self.quantity_decimals = tick_todecimals(contract_info['lotSize'])
            self.tick_size = contract_info['tickSize'] #ticksize: lowest allowed increment of a price change for orders (only decimals of .0 and .5 allowed on bitmex)
            self.lot_size = contract_info['lotSize'] 
    


class OrderStatus:
    def __init__(self, order_info, exchange):
        if exchange == "binance":
            self.order_id = order_info['orderId']
            self.status = order_info['status']
            self.avg_price = float(order_info['avgPrice'])
        
        elif exchange == "bitmex":
            self.order_id = order_info['orderId']
            self.status = order_info['ordStatus']
            self.avg_price = order_info['avgPx']
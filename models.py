
BITMEX_MULTIPLIER = 0.00000001

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
    def __init__(self, candle_info, exchange): #creating candel models for get_historical_candles() method
        if exchange == "binance": 
            self.timestamp = candle_info[0]
            self.open = candle_info['open']
            self.high = candle_info['high']
            self.low = candle_info['low']
            self.close = candle_info['close']
            self.volume = candle_info['volume']

        elif exchange == "bitmex": #keys are different for bitmex vs binanace
            self.timestamp = candle_info['timestamp']
            self.open = candle_info[1]
            self.high = float(candle_info[2])
            self.low = float(candle_info[3])
            self.close = float(candle_info[4])
            self.volume = float(candle_info[5])


class Contract: #creating contract models for get_contracts() method
    def __init__(self, contract_info, exchange):
        if exchange == "binance":
            self.symbol = contract_info['symbol']
            self.base_asset = contract_info['baseAsset']
            self.quote_asset = contract_info['quoteAsset']
            self.price_decimals = contract_info['pricePrecision'] #round price to decimal of an order accepted by Binance
            self.quantity_decimals = contract_info['quantityPrecision'] #round quantity to decimal of an order accepted by Binance
        
        elif exchange == "bitmex": #keys are different for bitmex vs binanace
            self.symbol = contract_info['symbol']
            self.base_asset = contract_info['rootSymbol']
            self.quote_asset = contract_info['quoteCurrency']
            self.price_decimals = contract_info['tickSize'] 
            self.quantity_decimals = contract_info['lotSize'] 
    


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
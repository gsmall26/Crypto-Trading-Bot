import logging
import pandas as pd
import time

from threading import Timer #can call function with a delay

from typing import *

from models import *

if TYPE_CHECKING:
    from connectors.bitmex import BitmexClient
    from connectors.binance import BinanceClient

logger = logging.getLogger()

TF_EQUIV = {"1m": 60, "5m": 300, "15m": 900, "30m": 1800, "1h": 3600, "4h": 14400} #timeframe equivalent in seconds


class Strategy:
    def __init__(self, client: Union["BitmexClient", "BinanceClient"], contract: Contract, exchange: str,
                timeframe: str, balance_pct: float, take_profit: float, stop_loss: float, strat_name):
        
        self.client = client #can call all methods from two connectors

        self.contract = contract
        self.exchange = exchange
        self.tf = timeframe
        self.tf_equiv = TF_EQUIV[timeframe] * 1000 #convert to milliseconds
        self.balance_pct = balance_pct
        self.take_profit = take_profit
        self.stop_loss = stop_loss

        self.strat_name = strat_name

        self.ongoing_position = False

        self.candles: List[Candle] = []
        self.trades: List[Trade] = []
        self.logs = []
    
    def _add_log(self, msg: str):
        logger.info("%s", msg)
        self.logs.append({"log": msg, "displayed": False})
    
    def parse_trades(self, price: float, size: float, timestamp: int) -> str:
        #3 cases: update same current candle, new candle, or new candle + missing candles

        timestamp_diff = int(time.time() * 1000) - timestamp
        if timestamp_diff >= 2000:
            logger.warning("%s %s: %s milliseconds of difference between the current time and the trade time", 
                    self.exchange, self.contract.symbol, timestamp_diff)

        last_candle = self.candles[-1]

        if timestamp < last_candle.timestamp + self.tf_equiv: #same candle
            last_candle.close = price #new price will be close/last price of the candle
            last_candle.volume += size

            if price > last_candle.high:
                last_candle.high = price
            elif price < last_candle.low:
                last_candle.low = price

            #check take profit / stop loss
            for trade in self.trades:
                if trade.status == "open" and trade.entry_price is not None:
                    self._check_tp_sl(trade)
            
            return "same_candle"

        elif timestamp >= last_candle.timestamp + 2 * self.tf_equiv: #missing candles
            
            missing_candles = int((timestamp - last_candle.timestamp) / self.tf_equiv) - 1 #how many we are missing

            logger.info("%s missing %s candles for %s %s (%s %s)", self.exchange, missing_candles, self.contract.symbol, self.tf, timestamp, last_candle.timestamp)

            for missing in range(missing_candles):
                new_ts = last_candle.timestamp + self.tf_equiv
                candle_info = {'ts': new_ts, 'open': last_candle.close, 'high': last_candle.close, 'low': last_candle.close, 'close': last_candle.close, 'volume': 0}
                
                new_candle = Candle(candle_info, self.tf, "parse_trade")

                self.candles.append(new_candle)

                last_candle = new_candle

            new_ts = last_candle.timestamp + self.tf_equiv
            candle_info = {'ts': new_ts, 'open': price, 'high': price, 'low': price, 'close': price, 'volume': size}
            new_candle = Candle(candle_info, self.tf, "parse_trade")

            self.candles.append(new_candle)

            return "new_candle"


        elif timestamp >= last_candle.timestamp + self.tf_equiv: #new candle
            new_ts = last_candle.timestamp + self.tf_equiv
            candle_info = {'ts': new_ts, 'open': price, 'high': price, 'low': price, 'close': price, 'volume': size}
            new_candle = Candle(candle_info, self.tf, "parse_trade")

            self.candles.append(new_candle)

            logger.info("%s New candle for %s %s", self.exchange, self.contract.symbol, self.tf)

            return "new_candle"

    def _check_order_status(self, order_id):
        order_status = self.client.get_order_status(self.contract, order_id)

        if order_status is not None:
            logger.info("%s order status: %s", self.exchange, order_status.status)

            if order_status.status == "filled":
                for trade in self.trades:
                    if trade.entry_id == order_id:
                        trade.entry_price = order_status.avg_price
                        trade.quantity = order_status.executed_qty
                        break
                return

        t = Timer(2.0, lambda: self._check_order_status(order_id))
        t.start()


    def _open_position(self, signal_result: int):

        if self.client.platform == "binance_spot" and signal_result == -1:
            return

        trade_size = self.client.get_trade_size(self.contract, self.candles[-1].close, self.balance_pct)
        if trade_size is None:
            return
        
        order_side = "buy" if signal_result == 1 else "sell"
        position_side = "long" if signal_result == 1 else "short"

        self._add_log(f"{position_side.capitalize()} signal on {self.contract.symbol} {self.tf}")

        order_status = self.client.place_order(self.contract, "MARKET", trade_size, order_side)

        if order_side is not None: #order is placed
            self._add_log(f"{order_side.capitalize()} order placed on {self.exchange} | Status: {order_status.status}")

            self.ongoing_position = True #true once order is placed

            avg_fill_price = None

            if order_status.status == "filled":
                avg_fill_price = order_status.avg_price
            else:
                t = Timer(2.0, lambda: self._check_order_status(order_status.order_id))
                t.start()
            
            new_trade = Trade({"time": int(time.time() * 1000), "entry_price": avg_fill_price, "contract": self.contract,
                               "strategy": self.strat_name, "side": position_side, "status": "open",
                               "pnl": 0, "quantity": order_status.executed_qty, "entry_id": order_status.order_id})
            self.trades.append(new_trade)
    
    def _check_tp_sl(self, trade: Trade): #take profit, stop loss

        tp_triggered = False
        sl_triggered = False

        price = self.candles[-1].close

        if trade.side == "long":
            if self.stop_loss is not None:
                if price <= trade.entry_price * (1 - self.stop_loss / 100): #stop loss exit price for long trade
                    sl_triggered = True
            
            if self.take_profit is not None:
                if price >= trade.entry_price * (1 + self.take_profit / 100): 
                    tp_triggered = True
        
        elif trade.side == "short":
            if self.stop_loss is not None:
                if price >= trade.entry_price * (1 + self.stop_loss / 100): #stop loss exit price for long trade
                    sl_triggered = True
            
            if self.take_profit is not None:
                if price <= trade.entry_price * (1 - self.take_profit / 100): 
                    tp_triggered = True
        
        if tp_triggered or sl_triggered:
            self._add_log(f"{'Stop loss' if sl_triggered else 'Take profit'} for {self.contract.symbol} {self.tf} "
                          f"| Current Price = {price} (Entry price was {trade.entry_price})")

            order_side = "SELL" if trade.side == "long" else "BUY"
            
            if not self.client.futures:
                current_balances = self.client.get_balances()
                if current_balances is not None:
                    if order_side == "SELL" and self.contract.base_asset in current_balances:
                        trade.quantity = min(current_balances[self.contract.base_asset].free, trade.quantity)

            order_status = self.client.place_order(self.contract, "MARKET", trade.quantity, order_side)

            if order_status is not None:
                self._add_log(f"Exit order on {self.contract.symbol} {self.tf} placed successfully")
                trade.status = "closed"
                self.ongoing_position = False



class TechnicalStrategy(Strategy):
    def __init__(self, client, contract: Contract, exchange: str, timeframe: str, balance_pct: float, take_profit: float, stop_loss: float, other_params: Dict):
        super().__init__(client, contract, exchange, timeframe, balance_pct, take_profit, stop_loss, "Technical")

        self._ema_fast = other_params['ema_fast']
        self._ema_slow = other_params['ema_slow']
        self._ema_signal = other_params['ema_signal']

        self._rsi_length = other_params['rsi_length']

    def _rsi(self) -> float: #relative strength index

        close_list = []
        for candle in self.candles:
            close_list.append(candle.close)

        closes = pd.Series(close_list)

        delta = closes.diff().dropna()

        up, down = delta.copy(), delta.copy()
        up[up < 0] = 0
        down[down > 0] = 0

        avg_gain = up.ewm(com=(self._rsi_length - 1), min_periods=self._rsi_length).mean() #com: Center of Mass
        avg_loss = down.abs().ewm(com=(self._rsi_length - 1), min_periods=self._rsi_length).mean()

        rs = avg_gain / avg_loss #relative strength

        rsi = 100 - 100 / (1 + rs)
        rsi = rsi.round(2)

        return rsi.iloc[-2]

    
    def _macd(self) -> Tuple[float, float]: #moving average convergence-divergence. EMA: Exponential Moving Average
        #1. fast EMA calculation 2. slow EMA 3. fast EMA - slow EMA 4. EMA on result to 3

        close_list = []
        for candle in self.candles:
            close_list.append(candle.close)

        closes = pd.Series(close_list)

        #ewm for exponential weighted functions
        ema_fast = closes.ewm(span=self._ema_fast).mean() 
        ema_slow = closes.ewm(span=self._ema_slow).mean()

        macd_line = ema_fast - ema_slow
        macd_signal = macd_line.ewm(span=self._ema_signal).mean() #moving avg of macd line - depends on signal being above/below signal line

        return macd_line.iloc[-2], macd_signal.iloc[-2] #-1 represents new one, not one just finished

    def _check_signal(self):

        macd_line, macd_signal = self._macd()
        rsi = self._rsi()

        # print(rsi, macd_line, macd_signal)

        if rsi < 30 and macd_line > macd_signal: #contract is oversold
            return 1

        elif rsi > 70 and macd_line < macd_signal: #contract is overbought
            return -1 #short

        else:
            return 0

    def check_trade(self, tick_type: str):
        #check only when new candle
        if tick_type == "new_candle" and not self.ongoing_position:
            signal_result = self._check_signal()

            if signal_result in [1, -1]:
                self._open_position(signal_result)


class BreakoutStrategy(Strategy):
    def __init__(self, client, contract: Contract, exchange: str, timeframe: str, balance_pct: float, take_profit: float, stop_loss: float, other_params: Dict):
        super().__init__(client, contract, exchange, timeframe, balance_pct, take_profit, stop_loss, "Breakout")

        self._min_volume = other_params['min_volume']

    def _check_signal(self) -> int:

        if self.candles[-1].close > self.candles[-2].high and self.candles[-1].volume > self._min_volume: #long signal: 1
            return 1

        elif self.candles[-1].close < self.candles[-2].low and self.candles[-1].volume > self._min_volume: #short signal: -1
            return -1

        else: #no signal: 0
            return 0
    

    def check_trade(self, tick_type: str):
        
        if not self.ongoing_position:
            signal_result = self._check_signal()

            if signal_result in [1, -1]:
                self._open_position(signal_result)


        
       
            

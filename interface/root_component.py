import tkinter as tk
from tkinter.messagebox import askquestion
import logging
import json

from connectors.bitmex import BitmexClient
from connectors.binance import BinanceClient

from interface.styling import * #access variables in styling file
from interface.logging_component import Logging
from interface.watchlist_component import Watchlist
from interface.trades_component import TradesWatch
from interface.strategy_component import StrategyEditor

logger = logging.getLogger()

class Root(tk.Tk): #root class will inherit from tk.Tk() class
    def __init__(self, binance: BinanceClient, bitmex: BitmexClient) -> None:
        super().__init__() #call to constructor of the parent class tk.Tk

        self.binance = binance
        self.bitmex = bitmex

        self.title("Trading Bot") #label, name seen at top of display
        self.protocol("WM_DELETE_WINDOW", self._ask_before_close)

        self.configure(bg=BG_COLOR) #altering background of root window

        self.main_menu = tk.Menu(self)
        self.configure(menu=self.main_menu)

        self.workspace_menu = tk.Menu(self.main_menu, tearoff=False)
        self.main_menu.add_cascade(label="Workspace", menu=self.workspace_menu)
        self.workspace_menu.add_command(label="Save workspace", command=self._save_workspace)

        #left and right split by creating two frames in the root component
        self._left_frame = tk.Frame(self, bg=BG_COLOR) #self = root
        self._left_frame.pack(side=tk.LEFT)

        self._right_frame = tk.Frame(self, bg=BG_COLOR) #self = root
        self._right_frame.pack(side=tk.LEFT) #left has priority

        self._watchlist_frame = Watchlist(self.binance.contracts, self.bitmex.contracts, self._left_frame, bg=BG_COLOR)
        self._watchlist_frame.pack(side=tk.TOP)

        self.logging_frame = Logging(self._left_frame, bg=BG_COLOR) #parent widget is left fraome
        self.logging_frame.pack(side=tk.TOP)

        self._strategy_frame = StrategyEditor(self, self.binance, self.bitmex, self._right_frame, bg=BG_COLOR)
        self._strategy_frame.pack(side=tk.TOP)

        self._trades_frame = TradesWatch(self._right_frame, bg=BG_COLOR)
        self._trades_frame.pack(side=tk.TOP)

        self._update_ui()

        #test that displays message to log: self.logging_frame.add_log("This is a test message")

    def _ask_before_close(self): 
        result = askquestion("Confirmation", "Do you really want to exit the application?") #whether user wants to close the application
        if result == "yes":
            self.binance.reconnect = False
            self.bitmex.reconnect = False

            self.binance.ws.close()
            self.bitmex.ws.close()

            self.destroy()
        

    def _update_ui(self):
        #logs

        #bitmex
        for log in self.bitmex.logs:
            if not log['displayed']: #if the element has not been displayed, add log to the logging component
                self.logging_frame.add_log(log['log'])
                log['displayed'] = True #it has now been added
        
        #binance
        for log in self.binance.logs:
            if not log['displayed']: #if the element has not been displayed, add log to the logging component
                self.logging_frame.add_log(log['log'])
                log['displayed'] = True #it has now been added
        
        #trades and logs
        for client in [self.binance, self.bitmex]:

            try:
                for b_index, strat in client.strategies.items():
                    for log in strat.logs:
                        if not log['dispalyed']:
                            self.logging_frame.add_log(log['log'])
                            log['displayed'] = True

                    for trade in strat.trades:
                        if trade.time not in self._trades_frame.body_widgets['symbol']:
                            self._trades_frame.add_trade(trade)

                        if trade.contract.exchange == "binance":
                            precision = trade.contract.price_decimals
                        else:
                            precision = 8 #pnl will always be in bitcoin

                        pnl_str = "{0:.{prec}f}".format(trade.pnl, prec=precision)
                        self._trades_frame.body_widgets['pnl_var'][trade.time].set(pnl_str)
                        self._trades_frame.body_widgets['status_var'][trade.time].set(trade.status.capitalize())
                        

            except RuntimeError as e:
                logger.error("Error while looping through strategies dictionary: %s", e)

        #watchlist prices
        try:
            for key, value in self._watchlist_frame.body_widgets['symbol'].items():

                symbol = self._watchlist_frame.body_widgets['symbol'][key].cget("text")
                exchange = self._watchlist_frame.body_widgets['exchange'][key].cget("text")
                
                if exchange == "Binance":
                    if symbol not in self.binance.contracts:
                        continue

                    if symbol not in self.binance.prices: #check that prices dictionary has key with our symbol
                        self.binance.get_bid_ask(self.binance.contracts[symbol])
                        continue
                    
                    precision = self.binance.contracts[symbol].price_decimals

                    prices = self.binance.prices[symbol] #temp variable
                
                elif exchange == "Bitmex":
                    if symbol not in self.bitmex.contracts:
                        continue

                    if symbol not in self.bitmex.prices: #check that prices dictionary has key with our symbol
                        continue

                    precision = self.bitmex.contracts[symbol].price_decimals

                    prices = self.bitmex.prices[symbol] #temp variable
                
                else: #potential typo
                    continue
                
                if prices['bid'] is not None:
                    price_str = "{0:.{prec}f}".format(prices['bid'], prec=precision)
                    self._watchlist_frame.body_widgets['bid_var'][key].set(price_str)

                if prices['ask'] is not None:
                    price_str = "{0:.{prec}f}".format(prices['ask'], prec=precision)
                    self._watchlist_frame.body_widgets['ask_var'][key].set(price_str)

        except RuntimeError as e:
            logger.error("Error while looping through watchlist dictionary: %s", e)

        self.after(1500, self._update_ui)


    def _save_workspace(self):

        #watchlist
        watchlist_symbols = []

        for key, value in self._watchlist_frame.body_widgets['symbol'].items():
            symbol = value.cget("text")
            exchange = self._watchlist_frame.body_widgets['exchange'][key].cget("text")

            watchlist_symbols.append((symbol, exchange))

        self._watchlist_frame.db.save("watchlist", watchlist_symbols)

        #strategies

        strategies = []

        strat_widgets = self._strategy_frame.body_widgets
        
        for b_index in strat_widgets['contract']:

            strategy_type = strat_widgets['strategy_type_var'][b_index].get()
            contract = strat_widgets['contract_var'][b_index].get()
            timeframe = strat_widgets['timeframe_var'][b_index].get()
            balance_pct = strat_widgets['balance_pct'][b_index].get()
            take_profit = strat_widgets['take_profit'][b_index].get()
            stop_loss = strat_widgets['stop_loss'][b_index].get()

            extra_params = {}

            for param in self._strategy_frame._extra_params[strategy_type]:
                code_name = param['code_name']

                extra_params[code_name] = self._strategy_frame.additional_parameters[b_index][code_name]

            strategies.append((strategy_type, contract, timeframe, balance_pct, take_profit, stop_loss,
                                json.dumps(extra_params),))
        
        self._strategy_frame.db.save("strategies", strategies)

        self.logging_frame.add_log("Workspace saved")


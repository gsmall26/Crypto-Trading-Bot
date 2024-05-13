import tkinter as tk
import logging

from connectors.bitmex import BitmexClient
from connectors.binance_futures import BinanaceFuturesClient

from interface.styling import * #access variables in styling file
from interface.logging_component import Logging
from interface.watchlist_component import Watchlist

logger = logging.getLogger()

class Root(tk.Tk): #root class will inherit from tk.Tk() class
    def __init__(self, binance: BinanaceFuturesClient, bitmex: BitmexClient) -> None:
        super().__init__() #call to constructor of the parent class tk.Tk

        self.binance = binance
        self.bitmex = bitmex

        self.title("Trading Bot") #label, name seen at top of display

        self.configure(bg=BG_COLOR) #altering background of root window

        #left and right split by creating two frames in the root component
        self._left_frame = tk.Frame(self, bg=BG_COLOR) #self = root
        self._left_frame.pack(side=tk.LEFT)

        self._right_frame = tk.Frame(self, bg=BG_COLOR) #self = root
        self._right_frame.pack(side=tk.LEFT) #left has priority

        self._watchlist_frame = Watchlist(self.binance.contracts, self.bitmex.contracts, self._left_frame, bg=BG_COLOR)
        self._watchlist_frame.pack(side=tk.TOP)

        self._logging_frame = Logging(self._left_frame, bg=BG_COLOR) #parent widget is left fraome
        self._logging_frame.pack(side=tk.TOP)

        self._update_ui()

        #test that displays message to log: self._logging_frame.add_log("This is a test message")

    def _update_ui(self):
        #logs

        #bitmex
        for log in self.bitmex.logs:
            if not log['displayed']: #if the element has not been displayed, add log to the logging component
                self._logging_frame.add_log(log['log'])
                log['displayed'] = True #it has now been added
        
        #binance
        for log in self.binance.logs:
            if not log['displayed']: #if the element has not been displayed, add log to the logging component
                self._logging_frame.add_log(log['log'])
                log['displayed'] = True #it has now been added

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




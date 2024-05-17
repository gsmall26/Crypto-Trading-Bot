import tkinter as tk
import typing
import tkmacosx as tkmac

from models import *

from interface.styling import *
from interface.autocomplete_widget import Autocomplete


class Watchlist(tk.Frame):
    def __init__(self, binance_contracts: typing.Dict[str, Contract], bitmex_contracts: typing.Dict[str, Contract], *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.binance_symbols = list(binance_contracts.keys())
        self.bitmex_symbols = list(bitmex_contracts.keys())
        
        self._commands_frame = tk.Frame(self, bg=BG_COLOR)
        self._commands_frame.pack(side=tk.TOP)

        self._table_frame = tk.Frame(self, bg=BG_COLOR)
        self._table_frame.pack(side=tk.TOP)

        #creating the two labels for each exchange
        self._binance_label = tk.Label(self._commands_frame, text="Binance", bg=BG_COLOR, fg=FG_COLOR, font=BOLD_FONT)
        self._binance_label.grid(row=0, column=0)

        self._binance_entry = Autocomplete(self.binance_symbols, self._commands_frame, fg=FG_COLOR, justify=tk.CENTER, insertbackground=FG_COLOR, bg=BG_COLOR_2, highlightthickness=False)
        self._binance_entry.bind("<Return>", self._add_binance_symbol) #when user presses return, trigger that function
        self._binance_entry.grid(row=1, column=0)

        self._bitmex_label = tk.Label(self._commands_frame, text="Bitmex", bg=BG_COLOR, fg=FG_COLOR, font=BOLD_FONT)
        self._bitmex_label.grid(row=0, column=1)

        self._bitmex_entry = Autocomplete(self.bitmex_symbols, self._commands_frame, fg=FG_COLOR, justify=tk.CENTER, insertbackground=FG_COLOR, bg=BG_COLOR_2, highlightthickness=False)
        self._bitmex_entry.bind("<Return>", self._add_bitmex_symbol) #when user presses return, trigger that function
        self._bitmex_entry.grid(row=1, column=1)

        self.body_widgets = {}

        self._headers = ["symbol", "exchange", "bid", "ask", "remove"]

        for idx, h in enumerate(self._headers): #access position (idx) and value (h)
            header = tk.Label(self._table_frame, text=h.capitalize() if h!="remove" else "", bg=BG_COLOR, fg=FG_COLOR, font=BOLD_FONT)
            header.grid(row=0, column=idx)

        for h in self._headers:
            self.body_widgets[h] = {}
            if h in ["bid", "ask"]:
                self.body_widgets[h + "_var"] = {}

            self._body_index = 1 #starts at 1

    def _remove_symbol(self, b_index: int):

        for h in self._headers:
            self.body_widgets[h][b_index].grid_forget()
            del self.body_widgets[h][b_index]

    def _add_binance_symbol(self, event):
        symbol = event.widget.get()

        if symbol in self.binance_symbols: #if there is incorrect input, widget will still contain symbol name
            self._add_symbol(symbol, "Binance")
            event.widget.delete(0, tk.END) #delete the entire content of the widget

    def _add_bitmex_symbol(self, event):
        symbol = event.widget.get()

        if symbol in self.bitmex_symbols:
            self._add_symbol(symbol, "Bitmex")
            event.widget.delete(0, tk.END)

    def _add_symbol(self, symbol: str, exchange: str):

        b_index = self._body_index

        self.body_widgets['symbol'][b_index] = tk.Label(self._table_frame, text=symbol, bg=BG_COLOR, fg=FG_COLOR_2, font=GLOBAL_FONT)
        self.body_widgets['symbol'][b_index].grid(row=b_index, column=0)

        self.body_widgets['exchange'][b_index] = tk.Label(self._table_frame, text=exchange, bg=BG_COLOR, fg=FG_COLOR_2, font=GLOBAL_FONT)
        self.body_widgets['exchange'][b_index].grid(row=b_index, column=1)

        #since bid and ask will be changing, the textvariable must be a tkinter StringVar object
        self.body_widgets['bid_var'][b_index] = tk.StringVar()
        self.body_widgets['bid'][b_index] = tk.Label(self._table_frame, textvariable=self.body_widgets['bid_var'][b_index], bg=BG_COLOR, fg=FG_COLOR_2, font=GLOBAL_FONT)
        self.body_widgets['bid'][b_index].grid(row=b_index, column=2)

        self.body_widgets['ask_var'][b_index] = tk.StringVar()
        self.body_widgets['ask'][b_index] = tk.Label(self._table_frame, textvariable=self.body_widgets['ask_var'][b_index], bg=BG_COLOR, fg=FG_COLOR_2, font=GLOBAL_FONT)
        self.body_widgets['ask'][b_index].grid(row=b_index, column=3)

        self.body_widgets['remove'][b_index] = tkmac.Button(self._table_frame, text="X", borderless=True, bg="darkred", fg=FG_COLOR, font=GLOBAL_FONT, command=lambda: self._remove_symbol(b_index)) #command tells us what to do once button is clicked. lambda prevents it from triggering right away
        self.body_widgets['remove'][b_index].grid(row=b_index, column=4)

        self._body_index += 1
        

        


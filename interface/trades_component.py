import tkinter as tk
import typing
import datetime

from models import *

from interface.styling import *
from interface.scrollable_frame import ScrollableFrame


class TradesWatch(tk.Frame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.body_widgets = {}

        self._headers = ["time", "symbol", "exchange", "strategy", "side", "quantity", "status", "pnl"]

        self._table_frame = tk.Frame(self, bg=BG_COLOR)
        self._table_frame.pack(side=tk.TOP)

        self._col_width = 11

        self._headers_frame = tk.Frame(self._table_frame, bg=BG_COLOR)

        for idx, h in enumerate(self._headers): #access position (idx) and value (h)
            header = tk.Label(self._headers_frame, text=h.capitalize(), bg=BG_COLOR, fg=FG_COLOR, font=GLOBAL_FONT, width=self._col_width)
            header.grid(row=0, column=idx)

        header = tk.Label(self._headers_frame, text="", bg=BG_COLOR, fg=FG_COLOR, font=GLOBAL_FONT, width=2)
        header.grid(row=0, column=len(self._headers))

        self._headers_frame.pack(side=tk.TOP, anchor="nw")

        self._body_frame = ScrollableFrame(self, bg=BG_COLOR, height=250)
        self._body_frame.pack(side=tk.TOP, anchor="nw", fill=tk.X)

        for h in self._headers:
            self.body_widgets[h] = {}
            if h in ["status", "pnl", "quantity"]:
                self.body_widgets[h + "_var"] = {}

        self._body_index = 0
    
    def add_trade(self, trade: Trade):

        b_index = self._body_index #current row number

        t_index = trade.time #in milliseconds

        dt_str = datetime.datetime.fromtimestamp(trade.time / 1000).strftime("%b %d %H:%M")

        self.body_widgets['time'][t_index] = tk.Label(self._body_frame.sub_frame, text=dt_str, bg=BG_COLOR, fg=FG_COLOR_2, font=GLOBAL_FONT, width=self._col_width)
        self.body_widgets['time'][t_index].grid(row=b_index, column=0)

        #symbol
        self.body_widgets['symbol'][t_index] = tk.Label(self._body_frame.sub_frame, text=trade.contract.symbol, bg=BG_COLOR, fg=FG_COLOR_2, font=GLOBAL_FONT, width=self._col_width)
        self.body_widgets['symbol'][t_index].grid(row=b_index, column=1)

        #exchange
        self.body_widgets['exchange'][t_index] = tk.Label(self._body_frame.sub_frame, text=trade.contract.exchange.capitalize(), bg=BG_COLOR, fg=FG_COLOR_2, font=GLOBAL_FONT, width=self._col_width)
        self.body_widgets['exchange'][t_index].grid(row=b_index, column=2)

        #strategy
        self.body_widgets['strategy'][t_index] = tk.Label(self._body_frame.sub_frame, text=trade.strategy, bg=BG_COLOR, fg=FG_COLOR_2, font=GLOBAL_FONT, width=self._col_width)
        self.body_widgets['strategy'][t_index].grid(row=b_index, column=3)

        #side
        self.body_widgets['side'][t_index] = tk.Label(self._body_frame.sub_frame, text=trade.side.capitalize(), bg=BG_COLOR, fg=FG_COLOR_2, font=GLOBAL_FONT, width=self._col_width)
        self.body_widgets['side'][t_index].grid(row=b_index, column=4)

        #quantity
        self.body_widgets['quantity'][t_index] = tk.Label(self._body_frame.sub_frame, text=trade.quantity, bg=BG_COLOR, fg=FG_COLOR_2, font=GLOBAL_FONT, width=self._col_width)
        self.body_widgets['quantity'][t_index].grid(row=b_index, column=5)

        #status
        self.body_widgets['status_var'][t_index] = tk.StringVar()
        self.body_widgets['status'][t_index] = tk.Label(self._body_frame.sub_frame, textvariable=self.body_widgets['status_var'][t_index], bg=BG_COLOR, fg=FG_COLOR_2, font=GLOBAL_FONT, width=self._col_width)
        self.body_widgets['status'][t_index].grid(row=b_index, column=6)

        #pnl
        self.body_widgets['pnl_var'][t_index] = tk.StringVar()
        self.body_widgets['pnl'][t_index] = tk.Label(self._body_frame.sub_frame, textvariable=self.body_widgets['pnl_var'][t_index], bg=BG_COLOR, fg=FG_COLOR_2, font=GLOBAL_FONT, width=self._col_width)
        self.body_widgets['pnl'][t_index].grid(row=b_index, column=7)

        self._body_index += 1
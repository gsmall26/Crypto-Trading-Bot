import tkinter as tk
from datetime import datetime

from interface.styling import *

#inherits from Frame class/widget
class Logging(tk.Frame):
    def __init__(self, *args, **kwargs) -> None:
        #frame gets instantiated when being passed in something like (self._left_frame, bg=BG_COLOR)
        super().__init__(*args, **kwargs) #*args lets us pass in arguments without specifying the name, kwargs let us pass in keyword arguments like bg=BG_COLOR

        self.logging_text = tk.Text(self, height=10, width=60, state=tk.DISABLED, bg=BG_COLOR, 
                                    fg=FG_COLOR_2, font=GLOBAL_FONT, highlightthickness=False) #self designates the frame, height = # of lines, state=locked or not; have to unlock when writing to widget
        self.logging_text.pack(side=tk.TOP) #places widget in the frame

    #add new log
    def add_log(self, message: str):
        self.logging_text.configure(state=tk.NORMAL)

        # %a gives first 3 letters of weekday, H:M:S, :: separates time and message
        self.logging_text.insert("1.0", datetime.now().strftime("%a %H:%M:%S :: ") + message + "\n") #1.0 -> text in beginning, tk.END -> text in end
        self.logging_text.configure(state=tk.DISABLED)
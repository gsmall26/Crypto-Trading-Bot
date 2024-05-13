import tkinter as tk

from interface.styling import * #access variables in styling file

class Root(tk.Tk): #root class will inherit from tk.Tk() class
    def __init__(self) -> None:
        super().__init__() #call to constructor of the parent class tk.Tk
        self.title("Trading Bot") #label, name seen at top of display

        self.configure(bg=BG_COLOR) #altering background of root window

        #left and right split by creating two frames in the root component
        self.left_frame = tk.Frame(self, bg=BG_COLOR) #self = root
        self.left_frame.pack(side=tk.LEFT)

        self.right_frame = tk.Frame(self, bg=BG_COLOR) #self = root
        self.right_frame.pack(side=tk.LEFT) #left has priority
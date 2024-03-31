import tkinter as tk
import logging #logging library

from connectors.binance_futures import BinanaceFuturesClient

logger = logging.getLogger() # logger object

logger.setLevel(logging.INFO)

stream_handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s %(levelname)s :: %(message)s') #format of the output messages
stream_handler.setFormatter(formatter)
stream_handler.setLevel(logging.INFO)

file_handler = logging.FileHandler('info.log') #create filer handler: to save logs to file
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.DEBUG)

#add to logger instance
logger.addHandler(stream_handler)
logger.addHandler(file_handler)


if __name__ == '__main__':

    binance = BinanaceFuturesClient(True) #using testnet environment
    print(binance.get_historical_candles('BTCUSDT', "1h"))

    root = tk.Tk() # root/main window
    root.mainloop() # displays root window


# logger.debug("This message is important noly when debugging the program")
# logger.info("This message just shows basic information")
# logger.warning("This message is about something you should pay attention to")
# logger.error("This message helps to debug an error that occurred in your program")

"""
old code
root.configure(bg="gray12") #

i = 0 #row number, first widget will be placed on first row
j = 0 #column number

calibri_font = ("Calibri", 11, "normal") #font family, font size, weight of font (normal/bold)

for contract in bitmex_contracts:
    label_widget = tk.Label(root, text=contract, bg='gray12', fg='SteelBlue1', width=13, font=calibri_font) #label object, takes in the root window. parent window of our widget. text is the contract name
    label_widget.grid(row=i, column=j, sticky='ew') #specify column and row number of each widget. column will always be 0. sticky tells us for widget to take up space on east and west (left and right)
    #pack() takes in side (tk.TOP/BOTTOM etc)

    if i == 4: # max row number for each column is 5. after 5, create new column
        j += 1
        i = 0
    else:
        i += 1
"""
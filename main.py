import tkinter as tk
import logging #logging library

from connectors.binance import BinanceClient
from connectors.bitmex import BitmexClient

from interface.root_component import Root

logger = logging.getLogger() # logger object

logger.setLevel(logging.INFO) #minimum logging level

stream_handler = logging.StreamHandler() #configure logging messages displayed in terminal
formatter = logging.Formatter('%(asctime)s %(levelname)s :: %(message)s') #format of the output messages
stream_handler.setFormatter(formatter)
stream_handler.setLevel(logging.INFO)

file_handler = logging.FileHandler('info.log') #create filer handler: to save logs to file
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.DEBUG)

#add to logger instance
logger.addHandler(stream_handler)
logger.addHandler(file_handler)

#entry point to application
if __name__ == '__main__':

    binance = BinanceClient("6b493fba6f464f92520a1df3c1a66b3271181ad16fe660cfa545838b60101360", #api keys from testnet.binancefuture
                                    "b316d432d1e251fa02ca3ae3267b333d96abdd86dbd90e569981b984d7ce33f0", testnet=True, futures=True) #using testnet environment. str, str, bool
    
    #bitmex = BitmexClient("uXr1T711wD-3pvEpXjlkvNFx", "GEIkARqi2QZh70V77T28M2Y0zxSBh_rNGhRJIbwZAIqYCkYu", True)
    bitmex = BitmexClient("necVI4HiTb733nqtBDKay0X_", "ftYXubQxLxdb_FBHbkj2CSTAJ1t6G_Fuf-61sV2Go8OHufBB", testnet=True)

    # print(bitmex.place_order(bitmex.contracts['XBTUSD'], "Limit", 50, "Buy", price=20000, tif="GoodTillCancel")) #example test
    
    #pass binace and bitmex objects into roo component
    root = Root(binance, bitmex) #initially tk.Tk(), root/main window
    root.mainloop() # displays root window


    #create Balance class and have a dict with currency as the key and the Balance object will be the value
    #Balance class will be a data model, meaning that we know exactly what is in there

    """
    example usage:
    print(binance.place_order("BTCUSDT", "BUY", 0.01, "LIMIT", 20000, "GTC")) - gtc = good til cancel
    print(binance.get_order_status("BTCUSDT", 3747638473))
    print(binance.cancel_order("BTCUSDT", 3747638473))
    """


# logger.debug("This message is important only when debugging the program")
# logger.info("This message just shows basic information")
# logger.warning("This message is about something you should pay attention to")
# logger.error("This message helps to debug an error that occurred in your program")

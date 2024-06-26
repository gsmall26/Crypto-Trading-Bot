import sqlite3
import typing


class WorkspaceData:
    def __init__(self) -> None:
        self.conn = sqlite3.connect("database.db") #create connection to database
        self.conn.row_factory = sqlite3.Row #when we get data, return list of SQLite row objects
        self.cursor = self.conn.cursor()

        self.cursor.execute("CREATE TABLE IF NOT EXISTS watchlist (symbol TEXT, exchange TEXT)")
        self.cursor.execute("CREATE TABLE IF NOT EXISTS strategies (strategy_type TEXT, contract TEXT,"
                            "timeframe TEXT, balance_pct REAL, take_profit REAL, stop_loss REAL, extra_params TEXT)")
                            
        self.conn.commit()

    def save(self, table: str, data: typing.List[typing.Tuple]): #inserts data to database
        #"INSERT INTO watchlist (symbol, exchange) VALUE (?, ?)"

        self.cursor.execute(f"DELETE FROM {table}")

        table_data = self.cursor.execute(f"SELECT * FROM {table}")

        columns = [description[0] for description in table_data.description] #columns of the table

        sql_statement = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({', '.join(['?'] * len(columns))})"

        self.cursor.executemany(sql_statement, data)
        self.conn.commit()
    
    def get(self, table: str) -> typing.List[sqlite3.Row]:
        self.cursor.execute(f"SELECT * FROM {table}")
        data = self.cursor.fetchall()

        return data
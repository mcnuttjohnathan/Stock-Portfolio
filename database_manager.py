'''
	Module handles all interactions with the programs database information
	
	@author Johnathan McNutt
'''
import sqlite3
from datetime import date

#database is set here for use in all internal functions
DATABASE = "null.db"

'''
	Creates the database tables for a new user account
'''
def createDatabase():
	conn = sqlite3.connect(DATABASE)
	
	curs = conn.cursor()
	
	curs.execute('''CREATE TABLE portfolio (
					symbol TEXT PRIMARY KEY,
					quantity_owned INTEGER
					)''')
					
	curs.execute('''CREATE TABLE transactions (
					symbol TEXT,
					type TEXT,
					quantity INTEGER,
					market_price INTEGER,
					market_date TEXT,
					FOREIGN KEY (symbol) REFERENCES portfolio(symbol)
					)''')
					
	curs.execute('''CREATE TABLE trends (
					symbol TEXT,
					market_price INTEGER,
					market_date TEXT,
					FOREIGN KEY (symbol) REFERENCES portfolio(symbol)
					)''')
					
	conn.commit()
	conn.close()

'''
	added stocks to the users portfolio. If the user already has stock of that
	symbol the function adds the quantities together
	
	@param symbol - the stocks NASDAQ symbol
	@param quantity_purchased - the amount of stock bought
'''
def addStockToPortfolio(symbol, quantity_purchased):
	#makes sure symbol conforms to database storing standard
	symbol = symbol.upper()

	conn = sqlite3.connect(DATABASE)
	
	curs = conn.cursor()
	
	curs.execute('''SELECT quantity_owned FROM portfolio 
					WHERE symbol=?''', (symbol,))
					
	check = curs.fetchone()
	
	#checks if primary key already exists
	if(check):
		#gets the quantity already owned
		quantity_owned = check[0]
	
		#updates the table adding the quantities together
		curs.execute('''UPDATE portfolio
						SET quantity_owned = ? + ?
						WHERE symbol = ?''', (quantity_owned, quantity_purchased, symbol))
	else:
		#creates a new entry for the symbol
		curs.execute('''INSERT INTO portfolio
						VALUES (?,?)''', (symbol, quantity_purchased))
						
	conn.commit()
	conn.close()

'''
	retrieves the quantity of stock owned for a specific stock symbol
	
	@param symbol - the NASDAQ stock symbol
	
	@return integer - quantity of stock owned
'''
def getAmountOwned(symbol):
	#makes sure symbol conforms to database storing standard
	symbol = symbol.upper()

	conn = sqlite3.connect(DATABASE)
	
	curs = conn.cursor()
	
	curs.execute('''SELECT quantity_owned FROM portfolio
					WHERE symbol=?''', (symbol,))				
	
	quantity = curs.fetchone()
	
	conn.close()
	
	if(not quantity):
		raise IndexError("no stock owned")
	
	#removes the quantity from list structure
	quantity = quantity[0]
	
	return quantity

'''
	retrieves the full portfolio for the current user
	
	@return list - all the entires in the portfolio table
'''
def getFullPortfolio():
	conn = sqlite3.connect(DATABASE)
	
	curs = conn.cursor()
	
	curs.execute('SELECT * FROM portfolio')
	
	portfolioList = curs.fetchall()
	
	conn.close()
	
	#checks if list is empty
	if(not portfolioList):
		raise IndexError("portfolio is empty")
	
	return portfolioList
	
'''
	removes stocks from the users portfolio. If all stock is sold entire is
	deleted from the table, otherwise quantity is simply altered
	
	@param symbol - the stocks NASDAQ symbol
	@param quantity_sold - the amount of stock sold
'''
def removeStockFromPortfolio(symbol, quantity_sold):
	#makes sure symbol conforms to database storing standard
	symbol = symbol.upper()

	conn = sqlite3.connect(DATABASE)
	
	curs = conn.cursor()
	
	#selects stock symbol entry to see if exists
	curs.execute('''SELECT quantity_owned FROM portfolio 
					WHERE symbol=?''', (symbol,))
					
	check = curs.fetchone()
	
	#checks if primary key already exists
	if(check):
		#gets the quantity already owned
		quantity_owned = check[0]
		
		if(quantity_owned > quantity_sold):
			#updates the table subtracting the sold stocks
			curs.execute('''UPDATE portfolio
							SET quantity_owned = ? - ?
							WHERE symbol = ?''', (quantity_owned, quantity_sold, symbol))
		elif(quantity_owned == quantity_sold):
			#deletes the stock from the portfolio
			curs.execute('''DELETE FROM portfolio
							WHERE symbol=?''', (symbol,))
			
			#removes trends data for stock that's no longer owned
			#not currently used, trends data persists
			#removeSymbolTrend(symbol)
		else:
			raise Exception('cannot sell more stock than you own')
	else:
		raise IndexError('Stock not owned')
		
	conn.commit()
	conn.close()
'''
	adds a new stock transaction to the transaction table
	
	@param symbol - the stocks NASDAQ symbol
	@param type - either 'buy' or 'sell'
	@param quantity - amount of stock bought or sold
	@param market_price - NASDAQ market price at time of transaction
	@param market_date - the date the transaction was made
'''
def addTransaction(symbol, type, quantity, market_price, market_date):
	#makes sure symbol conforms to database storing standard
	symbol = symbol.upper()

	conn = sqlite3.connect(DATABASE)
	
	curs = conn.cursor()
	
	curs.execute('''INSERT INTO transactions
					VALUES (?,?,?,?,?)''', (symbol, type, quantity, market_price, market_date))
	
	conn.commit()
	conn.close()
	
'''
	retrieves a list of the whole transactions table ordered by date of transaction
	
	@return list - ordered list of transactions
'''
def getAllTransactions():
	conn = sqlite3.connect(DATABASE)
	
	curs = conn.cursor()
	
	curs.execute('''SELECT * FROM transactions
					ORDER BY market_date''')
	
	transactionList = curs.fetchall()
	
	conn.close()
	
	if(not transactionList):
		raise IndexError("no transactions made")
	
	return transactionList

'''
	retrieves a list of all the transactions of the buy type
	
	@return list - list of all buy transactions
'''
def getBuyTransactions():
	conn = sqlite3.connect(DATABASE)
	
	curs = conn.cursor()
	
	curs.execute('''SELECT * FROM transactions
					WHERE type="buy"''')
					
	transactionList = curs.fetchall()
	
	conn.close()
	
	if(not transactionList):
		raise IndexError("no transactions made")
	
	return transactionList
	
'''
	retrieves a list of all the transactions of the sell type
	
	@return list - list of all sell transactions
'''
def getSellTransactions():
	conn = sqlite3.connect(DATABASE)
	
	curs = conn.cursor()
	
	curs.execute('''SELECT * FROM transactions
					WHERE type="sell"''')
					
	transactionList = curs.fetchall()
	
	conn.close()
	
	if(not transactionList):
		raise IndexError("no transactions made")
	
	return transactionList
	
'''
	retrieves a list of the quantities and prices of stocks bought
	for a specific symbol. Used for averaging prices
	
	@param symbol - the stocks NASDAQ symbol
	
	@return list - list of quantities and prices for a specific stock symbol
'''
def getSymbolBuyTransactions(symbol):
	#makes sure symbol conforms to database storing standard
	symbol = symbol.upper()
	
	conn = sqlite3.connect(DATABASE)
	
	curs = conn.cursor()
	
	curs.execute('''SELECT quantity, market_price FROM transactions
					WHERE symbol=? AND type="buy"''', (symbol,))
					
	transactionList = curs.fetchall()
	
	conn.close()
	
	if(not transactionList):
		raise IndexError("no transactions made")
	
	return transactionList
	
'''
	adds new stock trend data to the trends table
	
	@param symbol - the stocks NASDAQ symbol
	@param market_price - NASDAQ market price for the day
	@param market_date - the date the price was checked
'''
def addTrend(symbol, current_price, market_date):
	#makes sure symbol conforms to database storing standard
	symbol = symbol.upper()

	conn = sqlite3.connect(DATABASE)
	
	curs = conn.cursor()
	
	#checks whether todays trend data has already been added
	curs.execute('''SELECT * FROM trends
					WHERE symbol=? AND market_date=?''', (symbol, market_date,))
					
	check = curs.fetchall()
	
	#if a trend data has already been taken for the day trends data does not need to be inserted
	if(not check):
		curs.execute('''INSERT INTO trends
						VALUES (?,?,?)''', (symbol, current_price, market_date))
					
		conn.commit()
		
	conn.close()
	
'''
	removes a days trend data from the database, if it exists
	
	@param symbol - the stocks NASDAQ symbol
	@param market_date - the date the price was checked
'''
def removeTrend(symbol, market_date):
	#makes sure symbol conforms to database storing standard
	symbol = symbol.upper()

	conn = sqlite3.connect(DATABASE)
	
	curs = conn.cursor()
	
	#checks whether todays trend data exists
	curs.execute('''SELECT * FROM trends
					WHERE symbol=? AND market_date=?''', (symbol, market_date))
					
	check = curs.fetchall()
	
	if(check):
		curs.execute('''DELETE FROM trends
						WHERE symbol=? AND market_date=?''', (symbol, market_date))
	
'''
	retrieves all of the recorded prices for a given stock symbol
	
	@param symbol - the NASDAQ stock symbol
	
	@return list - trends information for a given symbol
'''
def getSymbolTrends(symbol):
	#makes sure symbol conforms to database storing standard
	symbol = symbol.upper()

	conn = sqlite3.connect(DATABASE)
	
	curs = conn.cursor()
	
	curs.execute('''SELECT * FROM trends
					WHERE symbol=?''', (symbol,))
					
	trendsList = curs.fetchall()
					
	conn.close()
	
	if(not trendsList):
		raise IndexError("no trends for symbol " + symbol)
	
	return trendsList
	
'''
	removes all trends data for a specific stock symbol
	
	@param symbol - the NASDAQ stock symbol to remove
'''
def removeSymbolTrend(symbol):
	#makes sure symbol conforms to database storing standard
	symbol = symbol.upper()

	conn = sqlite3.connect(DATABASE)
	
	curs = conn.cursor()
	
	#selection used to check if trends data exists
	curs.execute('''SELECT market_date FROM trends
					WHERE symbol=?''', (symbol,))
					
	check = curs.fetchone()
	
	#if data exists deletes it
	if(check):
		curs.execute('''DELETE FROM trends
						WHERE symbol=?''', (symbol,))
					
	conn.commit()
	conn.close()
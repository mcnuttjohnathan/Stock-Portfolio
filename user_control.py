'''	Module handles all user interactions with the program, primarily through logging
	the user into their personal database and then allowing them to select options from
	the programs main menu
	
	@author Johnathan McNutt
'''
import os
import re
import requests
import database_manager
import stock_model
from datetime import date

'''
	Handles program startup
'''
def stock_program():
	login()
	menuMain()

'''
	Allows the user to select the database they wish to use
	for the duration of the program
'''
def login():
	#loops until input matches regex
	valid = False
	while(not valid):
		database = input("Enter username: ")
		
		#checks that the username only contains letters
		valid = re.match('[a-zA-Z]', database)
		
		if(not valid):
			print("username may only contain letters\n")
	
	#adds the path and database extension
	database = "data/" + database + ".db"
	
	#sets the users database
	database_manager.DATABASE = database
	
	#creates the database tables if they don't already exist
	if(not os.path.exists(database)):
		database_manager.createDatabase()
		
	print()

'''
	Allows the user to select from menu options that handle different
	stock and database interactions such as buying stock, view portfolio,
	or quitting the program
'''
def menuMain():
	#below are constants representing main menu selections
	STOCK_PORTFOLIO = 	'p'
	BUY_STOCK = 		'b'
	SELL_STOCK = 		's'
	TRANSACTION_LOG =	'l'
	STOCK_TRENDS = 		't'
	QUIT = 				'q'

	select = -1
	
	while(select != QUIT):
		print("Stock Portfolio Simulation: Main Menu")
		print("p - stock portfolio")
		print("b - buy stocks")
		print("s - sell stocks")
		print("l - transaction log")
		print("t - stock trends")
		print("q - quit")
		
		select = input("Selection: ")
		
		print()
		
		#takes only the first character for checking
		select = select[0].lower()
		
		if(select == STOCK_PORTFOLIO):
			printPortfolio()
		elif(select == BUY_STOCK):
			buyStock()
		elif(select == SELL_STOCK):
			sellStock()
		elif(select == TRANSACTION_LOG):
			printLog()
		elif(select == STOCK_TRENDS):
			printTrends()
		elif(select == QUIT):
			exit(0)
		else:
			print("invalid selection")
			
		print()

'''
	Prints out information from the portfolio database table and displays
	gross and net worth
'''
def printPortfolio():
	try:
		print(stock_model.getPortfolioString())
	except IndexError:
		print("Portfolio is empty")
		
'''
	Checks the NASDAQ current price of stock by symbol and then allows the
	user to buy a quantity of the stock
'''
def buyStock():
	stock_model.buyStock()
	
'''
	Checks the NASDAQ current price of stock by symbol and then allows the
	user to sell a quantity of the stock
'''
def sellStock():
	stock_model.sellStock()

'''
	prints a log of the users transaction history ordered by date
'''
def printLog():
	try:
		print(stock_model.getTransactionString())
	except IndexError:
		print("No transactions made")
		
'''
	prints recorded trends for a specified stock symbol then gives
	the high, low, and average price
'''
def printTrends():
	symbol = input("Symbol of stock: ")
	
	print()
	
	try:
		print(stock_model.getSymbolTrendsString(symbol))
	except IndexError:
		print("No trends recorded for this symbol")
	
	
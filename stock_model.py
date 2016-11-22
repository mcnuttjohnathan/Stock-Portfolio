'''
	Module handles interactions with the NASDAQ stock website, buy and selling stock and
	presenting information about the users stock information that has already been stored
	in databases
	
	@author Johnathan McNutt
'''
from lxml import html
import requests
from datetime import date
import re
import math

import database_manager

NASDAQ_MONTHS = ["null", "Jan.", "Feb.", "Mar.", "Apr.", "May", "Jun.", "Jul.", "Aug.", "Sep.", "Oct.", "Nov.", "Dec."]

'''
	Checks the nasdaq website for the price on a specific
	stock via symbol and returns the current price in cents
	
	@param symbol - stock symbol representing a companies stock
	
	@return integer - the current price in cents
'''
def getCurrentPrice(symbol):
	url = 'http://www.nasdaq.com/symbol/' + symbol.lower()

	page = requests.get(url)
	tree = html.fromstring(page.content)
	
	page.close()

	#gets the days market price
	lastSale = tree.xpath('//div[@id="qwidget_lastsale"]/text()')
	
	#makes sure information was actually collected
	if(len(lastSale) == 0):
		raise ValueError(symbol + " is not a recognized stock symbol")
		
	#xpath returns lists, but only one entry for each item
	lastSale = lastSale[0]
	
	#price includes dollar sign which is removed
	lastSale = lastSale[1:]
	
	#converts price to integer cents to keep price accurate to money
	lastSale = float(lastSale)
	lastSale = (lastSale * 100) + .5 # .5 added to round off cents
	lastSale = int(lastSale)
	
	return lastSale
	
'''
	converts a price in integer cents to a string representing common dollar representation
	example: 100 cents would become $1.00
	
	@param cents - integer representing money in cents
	
	@returns string - the dollars string
'''
def getDollarsString(cents):
	if(cents < 10 and cents > 0):
		return "$0.0" + str(cents)
	
	if(cents < 100 and cents > 0):
		return "$0." + str(cents)

	dollars = str(cents)[:-2]
	change = str(cents)[-2:]
	
	#sign is blank unless number is negative
	sign = ''
	
	#checks if the number is negative
	if(dollars[0] == '-'):
		sign = '-'
		#removes minus sign to prevent it from interfering with comma placement
		dollars = dollars[1:]
	
	
	#separates the dollars into sets of three for comma placement
	dollarSegments = []
	while(len(dollars) > 3):
		dollarSegments.append(dollars[-3:])
		dollars = dollars[:-3]
	
	#adds the first set of numbers
	dollarSegments.append(dollars)
	
	#reverses the list for correct order
	dollarSegments = reversed(dollarSegments)
	
	#begins string construction
	message = sign
	message += '$'
	
	#adds commas between different magnitudes of dollars
	for segment in dollarSegments:
		message += segment + ','
	
	#removes final comma and replaces with a decimal point
	message = message[:-1]
	message += '.'
	
	#adds in the left over change
	message += change
	
	return message

'''
	Checks the NASDAQ current price of stock by symbol and then allows the
	user to buy a quantity of the stock
'''
def buyStock():
	symbol = input("Symbol of stock to purchase: ")
	
	print()
	
	try:
		price = getCurrentPrice(symbol)
		dollarsPrice = getDollarsString(price)
		
		print("Stock price is " + dollarsPrice + " per share")
		
		quantity = input("How many shares would you like to purchase? ")
		check = re.match('^[0-9]*$', quantity)
		if(check):
			quantity = int(quantity)
		
			if(quantity > 0):
				database_manager.addStockToPortfolio(symbol, quantity)
				database_manager.addTransaction(symbol, 'buy', quantity, price, date.today())
				database_manager.addTrend(symbol, price, date.today())
			else:
				print()
				print("cannot buy zero or less stocks")
		else:
			print()
			print("quantity must be a positive whole number")
	except requests.exceptions.ConnectionError:
		print("Couldn't connect to stock information. Please check internet connection")
	except ValueError:
		print("No stock information found for symbol " + symbol.upper())

'''
	Checks the NASDAQ current price of stock by symbol and then allows the
	user to sell a quantity of the stock
'''
def sellStock():
	symbol = input("Symbol of stock to sell: ")
	
	print()
	
	try:
		price = getCurrentPrice(symbol)
		dollarsPrice = getDollarsString(price)
		
		quantity_owned = database_manager.getAmountOwned(symbol.upper())
		
		print("Stock price is " + dollarsPrice + " per share")
		print("You own " + str(quantity_owned) + " shares")
		
		quantity = input("How many shares would you like to sell? ")
		check = re.match('^[0-9]*$', quantity)
		if(check):
			quantity = int(quantity)
			
			if(quantity_owned >= quantity and quantity > 0):
				database_manager.removeStockFromPortfolio(symbol, quantity)
				database_manager.addTransaction(symbol, 'sell', quantity, price, date.today())
				database_manager.addTrend(symbol, price, date.today())
			elif(quantity <= 0):
				print()
				print("Cannot sell zero or less stock")
			else:
				print()
				print("You cannot sell more stock than you have")
		else:
			print()
			print("quantity must be a positive whole number")
	except requests.exceptions.ConnectionError:
		print("Couldn't connect to stock information. Please check internet connection")
	except ValueError:
		print("No stock information found for symbol " + symbol.upper())
	
'''
	checks the NASDAQ websites current date against the computer clock date
	if they match returns true otherwise returns false
	
	@return boolean - whether dates match
'''
def checkDate():
	url = 'http://www.nasdaq.com/symbol/goog'
	
	page = requests.get(url)
	tree = html.fromstring(page.content)
	
	page.close()
	
	#gets today's market date
	marketDate = tree.xpath('//span[@id="qwidget_markettime"]/text()')
	marketDate = marketDate[0]
	
	day = date.today().day
	month = date.today().month
	year = date.today().year
	
	#organizes the computer date in the same schema as NASDAQ website
	computerDate = NASDAQ_MONTHS[month] + " " + str(day) + ", " + str(year)
	
	matching = re.match(computerDate, marketDate)
	
	if(matching):
		return True
		
	return False
	
'''
	assembles a string containing information on the users portfolio
	
	@return string - data about portfolio
'''
def getPortfolioString():
	message = "Stock Symbol\tQuantity Owned\tAverage Purchase\tCurrent Price\n"
	message += "-----------------------------------------------------------------------\n"
	
	portfolioList = database_manager.getFullPortfolio()
	
	#checks if portfolio is empty
	if(not portfolioList):
		raise IndexError("portfolio is empty")
	
	i = 0
	for i in range(0, len(portfolioList)):
		symbol = portfolioList[i][0]
		
		quantity = portfolioList[i][1]
		quantityString = '{:>14}'.format(str(quantity))
		
		averagePrice = getAveragePrice(symbol)
		averagePriceString = '{:>16}'.format(getDollarsString(averagePrice))
		
		currentPrice = getCurrentPrice(symbol)
		currentPriceString = '{:>13}'.format(getDollarsString(currentPrice))
		
		database_manager.addTrend(symbol, currentPrice, date.today())
		
		message += symbol + '\t\t' + quantityString + '\t' + averagePriceString + '\t' + currentPriceString + '\n'
		
	message += "-----------------------------------------------------------------------\n"
	
	portfolioValue = getPortfolioCurrentValue()
	portfolioValueString = '{:>20}'.format(getDollarsString(portfolioValue))
	
	sellTransactionTotal = getSellTransactionTotalValue()
	sellTransactionTotalString = '{:>20}'.format(getDollarsString(sellTransactionTotal))
	
	buyTransactionTotal = getBuyTransactionTotalValue()
	buyTransactionTotalString = '{:>20}'.format(getDollarsString(buyTransactionTotal))
	
	grossProfit = portfolioValue + sellTransactionTotal
	grossProfitString = '{:>20}'.format(getDollarsString(grossProfit))
	
	netProfit = grossProfit - buyTransactionTotal
	netProfitString = '{:>20}'.format(getDollarsString(netProfit))
	
	message += "  Total value of stocks sold:\t" + sellTransactionTotalString + "\n"
	message += "+ Today's portfolio value:\t" + portfolioValueString + "\n"
	message += "-----------------------------------------------------------------------\n"
	message += "  Gross Profit:\t\t\t" + grossProfitString + "\n"
	message += "- Total cost of stocks:\t\t" + buyTransactionTotalString + "\n"
	message += "-----------------------------------------------------------------------\n"
	message += "  Net Profit:\t\t\t" + netProfitString + "\n"
	
	return message

'''
	assembles a string containing information on the users transaction history
	
	@return string - data about transactions
'''
def getTransactionString():
	message = "Stock Symbol\tTrans Type\tQuantity\tMarket Price\tMarket Date\n"
	
	message += "---------------------------------------------------------------------------\n"
	
	transactionList = database_manager.getAllTransactions()
	
	if(not transactionList):
		raise Exception("no transactions made")
	
	i = 0
	for i in range(0, len(transactionList)):
		symbol = transactionList[i][0]
		
		type = transactionList[i][1]
		
		quantity = transactionList[i][2]
		quantityString = '{:>8}'.format(str(quantity))
		
		price = transactionList[i][3]
		priceString = '{:>12}'.format(getDollarsString(price))
		
		marketDate = transactionList[i][4]
		
		message += symbol + '\t\t' + type + '\t\t' + quantityString + '\t' + priceString + '\t' + marketDate + '\n'
	
	message += "---------------------------------------------------------------------------\n"
	
	return message
	
'''
	constructs a string displaying information on a stocks price over time by symbol
	
	@param symbol - the NASDAQ stock symbol
	
	@return string - data from the trends table
'''
def getSymbolTrendsString(symbol):
	message = "Market Price\tMarket Date\n"
	
	message += "-----------------------------------------------------------------------\n"
	
	trendsList = database_manager.getSymbolTrends(symbol)
	
	if(not trendsList):
		raise Exception("no trends recorded for symbol " + symbol)
	
	#a starting value lower than any possible unit stock price
	highestPrice = 0
	#a starting value higher than any possible unit stock price
	lowestPrice = 999999999
	
	sum = 0
	count = 0
	
	i = 0
	for i in range(0, len(trendsList)):
		marketPrice = trendsList[i][1]
		marketPriceString = '{:>12}'.format(getDollarsString(marketPrice))
		
		marketDate = trendsList[i][2]
		
		message += marketPriceString + '\t' + marketDate + '\n'
		
		if(marketPrice > highestPrice):
			highestPrice = marketPrice
		
		if(marketPrice < lowestPrice):
			lowestPrice = marketPrice
			
		sum += marketPrice
		
		count += 1
		
	message += "-----------------------------------------------------------------------\n"
	
	highestPriceString = '{:>10}'.format(getDollarsString(highestPrice))
	lowestPriceString = '{:>10}'.format(getDollarsString(lowestPrice))
	
	averagePrice = math.ceil(sum/count)
	averagePriceString = '{:>10}'.format(getDollarsString(averagePrice))
	
	message += "Highest Price:\t" + highestPriceString + '\n'
	message += "Lowest Price:\t" + lowestPriceString + '\n'
	message += "Average Price:\t" + averagePriceString + '\n'
		
	return message
		
		
	
'''
	retrieves the current value of the portfolio if all stocks were sold today
	
	@returns integer - the portfolios total value in cents
'''
def getPortfolioCurrentValue():
	portfolio = database_manager.getFullPortfolio()
	
	#returns 0 if portfolio is empty
	if(not portfolio):
		return 0
	
	sum = 0
	
	i = 0
	for i in range(0, len(portfolio)):
		symbol = portfolio[i][0]
		quantity = portfolio[i][1]
		
		currentPrice = getCurrentPrice(symbol)
		
		sum += quantity * currentPrice
		
	return sum

'''
	retrieves the total value of all buy transactions
	
	@return integer - the buy sum in cents
'''
def getBuyTransactionTotalValue():
	try:
		buyList = database_manager.getBuyTransactions()
	#returns 0 if no transactions made
	except IndexError:
		return 0
	
	sum = 0
	
	i = 0
	for i in range(0, len(buyList)):
		quantity = buyList[i][2]
		price = buyList[i][3]
		
		sum += quantity * price
		
	return sum
	
'''
	retrieves the total value of all sell transactions
	
	@return integer - the sell sum in cents
'''
def getSellTransactionTotalValue():
	try:
		sellList = database_manager.getSellTransactions()
	#returns 0 if no transactions made
	except IndexError:
		return 0
	
	sum = 0
	
	i = 0
	for i in range(0, len(sellList)):
		quantity = sellList[i][2]
		price = sellList[i][3]
		
		sum += quantity * price
		
	return sum
	
'''
	averages the price of all transactions by summing the quantity * price and
	dividing by the sum of all the quantities
	
	@param symbol - the stocks NASDAQ symbol
	
	@return integer - the average price in cents
'''
def getAveragePrice(symbol):
	priceList = database_manager.getSymbolBuyTransactions(symbol)

	#returns 0 if no transactions made
	if(not priceList):
		return 0
	
	#the numerator in the average equation
	sum = 0
	#the denominator in the average equation
	count = 0
	
	i = 0
	for i in range(0, len(priceList)):
		#adds the quantity times the price
		sum += priceList[i][0] * priceList[i][1]
		#adds the quantity
		count += priceList[i][0]
		
	averagePrice = math.ceil(sum/count)
		
	return averagePrice
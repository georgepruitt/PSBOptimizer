'''/////////////////////////////////////////////////////////////////////////////////
 System Tester.py - programmed by George Pruitt www.georgepruitt.com
 Copyright 2016 by George Pruitt
 Feel free to distribute and improve upon - just include this banner
 Version 2.1 scroll down about half way to get to your system coding section
///////////////////////////////////////////////////////////////////////////////////'''

#--------------------------------------------------------------------------------
#Import Section - inlcude functions, classes, variabels
#from external modules
#--------------------------------------------------------------------------------
import csv
import tkinter as tk
import os.path
from getData import getData
from dataLists import myDate,myTime,myOpen,myHigh,myLow,myClose
from tradeClass import tradeInfo
from equityDataClass import equityClass
from trade import trade
from systemMarket import systemMarketClass
from portfolio import portfolioClass
from indicators import highest,lowest,rsiClass,stochClass,sAverage,bollingerBands
from systemAnalytics import calcSystemResults
from tkinter.filedialog import askopenfilenames
#--------------------------------------------------------------------------------
  #End of Import Section
#--------------------------------------------------------------------------------

#--------------------------------------------------------------------------------
  #Helper Functions local to this module
#--------------------------------------------------------------------------------
def getDataAtribs(dClass):
   return(dClass.bigPtVal,dClass.symbol,dClass.minMove)
def getDataLists(dClass):
   return(dClass.date,dClass.open,dClass.high,dClass.low,dClass.close)
def roundToNearestTick(price,upOrDown,tickValue):
    temp1 = price - int(price)
    temp2 = int(temp1 / tickValue)
    temp3 = temp1 -(tickValue*temp2)
    if upOrDown == 1:
        temp4 = tickValue - temp3
        temp5 = temp1 + temp4
    if upOrDown == -1:
        temp4 = temp1 - temp3
        temp5 = temp4
    return(int(price) + temp5)

def calcTodaysOTE(mp,myClose,entryPrice,entryQuant,myBPV):
    todaysOTE = 0
    for entries in range(0,len(entryPrice)):
        if mp >= 1:
            todaysOTE += (myClose - entryPrice[entries])*myBPV*entryQuant[entries]
        if mp <= -1:
           todaysOTE += (entryPrice[entries] - myClose)*myBPV*entryQuant[entries]
    return(todaysOTE)

def exitPos(myExitPrice,myExitDate,tempName,myCurShares):
    global mp,commission
    global tradeName,entryPrice,entryQuant,exitPrice,numShares,myBPV,cumuProfit
    if mp < 0:
        trades = tradeInfo('liqShort',myExitDate,tempName,myExitPrice,myCurShares,0)
        profit = trades.calcTradeProfit('liqShort',mp,entryPrice,myExitPrice,entryQuant,myCurShares) * myBPV
        profit = profit - myCurShares *commission
        trades.tradeProfit = profit
        cumuProfit += profit
        trades.cumuProfit = cumuProfit
    if mp > 0:
        trades = tradeInfo('liqLong',myExitDate,tempName,myExitPrice,myCurShares,0)
        profit = trades.calcTradeProfit('liqLong',mp,entryPrice,myExitPrice,entryQuant,myCurShares) * myBPV
        profit = profit - myCurShares * commission
        trades.tradeProfit = profit
        cumuProfit += profit
        trades.cumuProfit = cumuProfit
    curShares = 0
    for remShares in range(0,len(entryQuant)):
       curShares += entryQuant[remShares]
    return (profit,trades,curShares)
#--------------------------------------------------------------------------------
  #End of functions
#--------------------------------------------------------------------------------

#---------------------------------------------------------------------------------
  #Lists and variables are defined and initialized here
#---------------------------------------------------------------------------------
alist, blist, clist, dlist, elist = ([] for i in range(5))
marketPosition,listOfTrades,trueRanges,ranges = ([] for i in range(4))
dataClassList,systemMarketList,equityDataList = ([] for i in range(3))
entryPrice,fileList,entryPrice,entryQuant,exitQuant = ([] for i in range(5))
#exitPrice = list()
currentPrice = 0
totComms = 0
barsSinceEntry = 0
numRuns = 0
myBPV = 0
allowPyr = 0
curShares = 0
#---------------------------------------------------------------------------------
  #End of Lists and Variables
#---------------------------------------------------------------------------------

#---------------------------------------------------------------------------------
  #Get the raw data and its associated attributes [pointvalue,symbol,tickvalue]
  #Read a csv file that has at least D,O,H,L,C - V and OpInt are optional
  #Set up a portfolio of multiple markets
#---------------------------------------------------------------------------------

dataClassList = getData()
numMarkets = len(dataClassList)
portfolio = portfolioClass()

#---------------------------------------------------------------------------------
 #Trade Accounting function used to reduce reduncancy
#---------------------------------------------------------------------------------
def bookTrade(entryOrExit,lOrS,price,date,tradeName,shares):
    global mp,commission,totProfit,curShares,barsSinceEntry,listOfTrades
    global entryPrice,entryQuant,exitPrice,numShares,myBPV,cumuProfit
    if entryOrExit == -1:
        profit,trades,curShares = exitPos(price,date,tradeName,shares)
        listOfTrades.append(trades)
        if curShares == 0 : mp = 0
        marketPosition[i] = mp
    else:
        profit = 0
        curShares = curShares + shares
        barsSinceEntry = 1
        entryPrice.append(price)
        entryQuant.append(shares)
        if lOrS == 1:
            mp += 1
            marketPosition[i] = mp
            trades = tradeInfo('buy',date,tradeName,entryPrice[-1],shares,1)
        if lOrS ==-1:
            mp -= 1
            marketPosition[i] = mp
            trades = tradeInfo('sell',date,tradeName,entryPrice[-1],shares,1)
        listOfTrades.append(trades)
    return(profit,curShares)


#---------------------------------------------------------------------------------
  #SET COMMISSION, NUMBER OF BARS TO BACK TEST, AND RAMP UP FOR INDICATORS
#---------------------------------------------------------------------------------

commission = 100 # deducted on a round turn basis
#numBarsToGoBack = 10000 # number of bars from the end of data
startTestDate = 19900101 #must be in yyyymmdd
rampUp = 100 # need this minimum of bars to calculate indicators
sysName = "DC" #System Name here
initCapital = 100000

optSpace = list()
optVar1 = (20,40,10)
optVar2 = (1000,3000,1000)
optVar1Runs = int(((optVar1[1] - optVar1[0]) / optVar1[2]) + 1)
optVar2Runs = int(((optVar2[1] - optVar2[0]) / optVar2[2]) + 1)
for x in range(optVar1Runs):
    for y in range(optVar2Runs):
        optSpace.append([optVar1[1] + optVar1[2] * x,optVar2[1] + optVar2[2] * y])
numOfRuns = optVar1Runs*optVar2Runs
totNumOfRuns = numOfRuns * numMarkets
print(optSpace)

marketCnt = 0

#////////  DO NOT CHANGE BELOW /////////////////////////////////////////////////
for runs in range(0,totNumOfRuns):
    listOfTrades[:] = []
    entryPrice[:] = []
    marketPosition[:] = []
    entryQuant[:] = []
    exitQuant[:] = []
    if runs % numOfRuns == 0:
        trueRanges[:] = []       
        myBPV,myComName,myMinMove = getDataAtribs(dataClassList[marketCnt])
        myDate,myOpen,myHigh,myLow,myClose = getDataLists(dataClassList[marketCnt])
        marketCnt = marketCnt + 1
        for i in range(0,len(myDate)):
            ranges.append(myHigh[i] - myLow[i])
            if i == 0:
                trueRanges.append(ranges[i])
            if i > 0:
                trueRanges.append(max(myClose[i-1],myHigh[i]) - min(myClose[i-1],myLow[i]))
    systemMarket = systemMarketClass()
    equity = equityClass()
    equItm = 0
    totProfit =0
    maxPositionL = 0
    maxPositionS = 0
    cumuProfit = 0
    curShares = 0
    numShares = 0
    longMMLoss = 99999999
    shortMMLoss = 0
    lenOfDates = len(myDate)
    marketPosition = [0 for i in range(lenOfDates)]
#    print(len(marketPosition))
##   if len(myDate) < numBarsToGoBack: numBarsToGoBack = len(myDate)
##    if numBarsToGoBack < rampUp: break
    barCount = 0
    while (myDate[barCount]) <= startTestDate:
        barCount +=1
    if barCount < rampUp:
        while barCount <= rampUp:
            barCount +=1

#////////  DO NOT CHANGE ABOVE /////////////////////////////////////////////////

#---------------------------------------------------------------------------------
#Instantiate Indicator Classes
#---------------------------------------------------------------------------------
    rsiStudy = rsiClass()
    stochStudy = stochClass()
#---------------------------------------------------------------------------------
    for i in range(barCount,len(myDate)):
#        donchLen = 20 + (runs - (marketCnt-1)) * 10
#        donchLen = optVar1[0] + (runs % numOfRuns) * optVar1[2]
        donchLen = optSpace[runs % numOfRuns][0]
        stopAmt = optSpace[runs % numOfRuns][1]/myBPV
        sysName = str(donchLen) + " - " + str(optSpace[runs % numOfRuns][1])
        equItm += 1
        tempDate = myDate[i]
        todaysCTE = todaysOTE = todaysEquity = 0
        if len(marketPosition) > 1 : marketPosition[i] = marketPosition[i-1]
        mp = marketPosition[i]
#        buyLevel,shortLevel,exitLevel = bollingerBands(myDate,myClose,60,2,i,1)
#        buyLevel = roundToNearestTick(buyLevel,1,myMinMove)
#        shortLevel = roundToNearestTick(shortLevel,-1,myMinMove)
        buyLevel = highest(myHigh,donchLen,i,1)
        shortLevel = lowest(myLow,donchLen,i,1)
        exitLevel = (buyLevel + shortLevel)/2
        
#        print(myDate[i]," buylevel ",buyLevel," shortlevel ",shortLevel)
        if mp == 1 : exitLevel = lowest(myLow,30,i,1)
        if mp == -1: exitLevel = highest(myHigh,30,i,1)

        # if mp ==  1 and (myHigh[-1] - exitLevel)*myBPV > 5000 : exitLevel = myHigh[i-1] - 2000/myBPV
        # if mp == -1 and (exitLevel - myLow[-1])*myBPV > 5000 : exitLevel = myLow[i-1] + 2000/myBPV

        # if mp == -1 and (myHigh[-1] - exitLevel)*myBPV > 5000 : print(myDate[i]," Long risk > 5000")
        # if mp == -1 and (exitLevel - myLow[-1])*myBPV > 5000 : print(myDate[i]," Short risk < 5000")


        atrVal = sAverage(trueRanges,10,i,0)
        rsiVal = rsiStudy.calcRsi(myClose,10,i,0)


 #Long Entry Logic
        if (mp == 0 or mp == -1)  and myHigh[i] >= buyLevel:
            profit = 0
            price = max(myOpen[i],buyLevel)
            if mp <= -1:
                profit,curShares = bookTrade(-1,0,price,myDate[i],"RevshrtLiq",curShares)
                todaysCTE = profit
            maxPositionProfLong = myHigh[i]
            tradeName = "Donch Buy"
            longMMLoss = price - stopAmt
            numShares = 1
            profit,curShares = bookTrade(1,1,price,myDate[i],tradeName,numShares)

 #Long Exit - Loss
        longLossPrice = max(longMMLoss,exitLevel)
        
        if mp >= 1 and myLow[i] <= longLossPrice and barsSinceEntry > 1:
            price = min(myOpen[i],longLossPrice)
            maxPositionProfLong = (maxPositionProfLong - entryPrice[-1]) *myBPV
            tradeName = "L-MMLoss"
            exitDate =myDate[i]
            numShares = curShares
            profit,curShares = bookTrade(-1,0,price,myDate[i],tradeName,numShares)
            totProfit += profit
            todaysCTE = profit
            maxPositionL = maxPositionL - 1

# Short Logic
        if (mp == 0 or mp == 1)  and myLow[i] <= shortLevel:
            profit = 0
            price = min(myOpen[i],shortLevel)
            if mp >= 1:
                profit,curShares = bookTrade(-1,0,price,myDate[i],"RevlongLiq",curShares)
                todaysCTE = profit
            tradeName = "Donch Short"
            shortMMLoss = price + stopAmt
            numShares = 1
            profit,curShares = bookTrade(1,-1,price,myDate[i],tradeName,numShares)

# Short Exit Loss
        shortLossPrice = min(shortMMLoss,exitLevel)
        if mp <= -1 and myHigh[i] >= shortLossPrice and barsSinceEntry > 1:
            price = max(myOpen[i],shortLossPrice)
            tradeName = "S-MMLoss"
            exitDate = myDate[i]
            numShares = curShares
            profit,curShares = bookTrade(-1,0,price,myDate[i],tradeName,numShares)
            todaysCTE = profit
            maxPositionL -= 1


 ###########  DO NOT CHANGE BELOW ################################################################
        if mp == 0 :
            todaysOTE = 0
            curShares = 0
            entryPrice[:] = []
            maxPositionL = 0
            maxPositionS = 0
        if mp != 0 :
            barsSinceEntry = barsSinceEntry + 1
            todaysOTE = calcTodaysOTE(mp,myClose[i],entryPrice,entryQuant,myBPV)
        todaysEquity = todaysOTE + totProfit
        equity.setEquityInfo(myDate[i],equItm,todaysCTE,todaysOTE)
    if mp >= 1:
        price = myClose[i]
        tradeName = "L-EOD"
        exitDate =myDate[i]
        numShares = curShares
        profit,curShares = bookTrade(-1,0,price,myDate[i],tradeName,numShares)

    if mp <= -1:
        price = myClose[i]
        tradeName = "S-EOD"
        exitDate =myDate[i]
        numShares = curShares
        profit,curShares = bookTrade(-1,0,price,myDate[i],tradeName,numShares)

    systemMarket.setSysMarkInfo(sysName,myComName,listOfTrades,equity,initCapital)
    systemMarketList.append(systemMarket)
    numRuns = numRuns + 1

if numMarkets > 0:
    portfolio.setPortfolioInfo("PortfolioTest",systemMarketList)
    calcSystemResults(systemMarketList)
if numMarkets == 0: print("No markets selected : terminating!")

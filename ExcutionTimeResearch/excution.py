import numpy as np
import pandas as pd
from collections import deque
from enum import Enum, unique
import time
from datetime import timedelta

pathOrder = './data/MyOrderSet.csv'
pathPrice = './data/SecondPriceSet.csv'

orderSet = pd.read_csv(pathOrder)
priceSet = pd.read_csv(pathPrice, index_col='Date')

orderSet['Time'] = pd.to_datetime(orderSet['Time'])
priceSet.index = pd.to_datetime(priceSet.index)
test = int(len(priceSet) / 2)
timeInterval = priceSet.index[:500]
print('1')
"""
Note: finding that convert the datetime in priceSet consumes lots of time
we first use
priceSet.index = pd.to_datetime(priceSet.index, format='%m/%d/%Y %H:%M:%S')
to convert the index
then we do
priceSet.to_csv(pathPrice)
save it, so that we can use it now
"""


class Excution:
    """"""
    def __init__(self, timeInterval, orderSet, priceSet):
        self.timeInterval = timeInterval
        self.orderSet = orderSet
        self.priceSet = priceSet
        self.maxSL = -0.05
        self.maxTTENum = 600
        self.maxTTE = timedelta(seconds=self.maxTTENum)

        self.mktData = None
        self.orderOngoing = {}
        self.orderCompleted = []

        self.orderSetPtr = 0
        self.marketType = None

    def backtest(self):

        for tick in self.timeInterval:
            self.readMktData(tick)
            self.getMarketType()
            self.checkNewOrder(tick)
            self.ExcuteOngoingOrder(tick)

    def readMktData(self, tick):

        bid, ask = self.priceSet.loc[tick, ['Bid', 'Ask']]
        self.mktData = MktData(bid, ask, tick)

    def checkNewOrder(self, tick):
        if self.orderSetPtr > len(self.orderSet) - 1:
            # out of index, no new order
            return

        if tick == self.orderSet.iloc[self.orderSetPtr]['Time']:
            direction = self.orderSet.iloc[self.orderSetPtr]['Side']
            newOrder = Order(direction, tick, self.mktData)
            newOrder = self.setCoverCondition(newOrder)
            newOrder = self.setExcutionTarget(newOrder)
            self.orderOngoing[tick] = newOrder
            self.orderSetPtr += 1

    def setCoverCondition(self, newOrder):
        """Set order cover condition.

        Set order cover condition according to market type.
        """
        # enforce using certain cover condition
        if self.marketType == MarketType.AlwaysMT:
            newOrder.coverCondition = CoverType(0)
        elif self.marketType == MarketType.AlwaysOMMSide:
            newOrder.coverCondition = CoverType(1)
        elif self.marketType == MarketType.AlwaysOMMid:
            newOrder.coverCondition = CoverType(2)

        return newOrder

    def setExcutionTarget(self, newOrder):
        """
        Set excution target bid or ask price
        """
        if newOrder.coverCondition == CoverType(0):
            if newOrder.direction == 'B':
                newOrder.targetAsk = self.mktData.Ask
                newOrder.targetBid = None
            elif newOrder.direction == 'S':
                newOrder.targetAsk = None
                newOrder.targetBid = self.mktData.Bid
        elif newOrder.coverCondition == CoverType(1):
            if newOrder.direction == 'B':
                newOrder.targetAsk = self.mktData.Bid
                newOrder.targetBid = None
            elif newOrder.direction == 'S':
                newOrder.targetAsk = None
                newOrder.targetBid = self.mktData.Ask
        elif newOrder.coverCondition == CoverType(2):
            if newOrder.direction == 'B':
                newOrder.targetAsk = (self.mktData.Ask + self.mktData.Bid) / 2
                newOrder.targetBid = None
            elif newOrder.direction == 'S':
                newOrder.targetAsk = None
                newOrder.targetBid = (self.mktData.Ask + self.mktData.Bid) / 2

        return newOrder

    def ExcuteOngoingOrder(self, tick):
        if not self.orderOngoing:
            return
        copydict = self.orderOngoing.copy()
        for k, v in copydict.items():
            thisOrder = v
            self.renewPnl(thisOrder, k)
            self.closeOngoingOrder(thisOrder, k)

    def renewPnl(self, thisOrder, k):
        if thisOrder.direction == 'B':
            thisOrder.OMMPnl = thisOrder.MTAsk - self.mktData.Ask
        elif thisOrder.direction == 'S':
            thisOrder.OMMPnl = self.mktData.Bid - thisOrder.MTBid

        thisOrder.Pnl = thisOrder.MTPnl + thisOrder.OMMPnl
        self.orderOngoing[k] = thisOrder

    def getMarketType(self):
        self.marketType = MarketType(100)  # TODO: change

    def closeOngoingOrder(self, thisOrder, k):
        if self.checkCoverCondition(thisOrder, k):
            self.closeOrder(k)
            return
        if self.checkLimit(thisOrder, k):
            self.closeOrder(k)
            return
        return

    def checkCoverCondition(self, thisOrder, k):
        if thisOrder.direction == 'B':
            if self.mktData.Ask <= thisOrder.targetAsk:
                return True
        elif thisOrder.direction == 'S':
            if self.mktData.Bid >= thisOrder.targetBid:
                return True
        return False

    def checkLimit(self, thisOrder, k):
        """"""
        if self.mktData.tick - thisOrder.recv_time > self.maxTTE:
            thisOrder.triggerTTE = True
        if thisOrder.OMMPnl < thisOrder.MTmidPrice * self.maxSL:
            thisOrder.triggerSL = True

        if thisOrder.triggerTTE or thisOrder.triggerSL:
            return True

        return False

    def closeOrder(self, k):
        order_closed = self.orderOngoing.pop(k)
        order_closed.excuteAsk = self.mktData.Ask
        order_closed.excuteBid = self.mktData.Bid
        order_closed.excu_time = self.mktData.tick
        self.orderCompleted.append(order_closed)

    def showResultSheet(self):
        """Show the sheet of performance."""
        # show completed order
        if not self.orderCompleted:
            return None
        columns = [
            'recv_time', 'Side', 'MTBid', 'MTAsk', 'CoverType', 'TargetBid',
            'TargetAsk', 'ExcuteBid', 'ExcuteAsk', 'OOMPnl', 'Pnl',
            'TriggerSL', 'TriggerTTE'
        ]
        dfResult = pd.DataFrame(index=range(len(self.orderCompleted)),
                                columns=columns)
        for i in range(len(self.orderCompleted)):
            thisOrder = self.orderCompleted[i]
            dfResult.loc[i, 'recv_time'] = thisOrder.recv_time
            dfResult.loc[i, 'Side'] = thisOrder.direction
            dfResult.loc[i, 'MTBid'] = thisOrder.MTBid
            dfResult.loc[i, 'MTAsk'] = thisOrder.MTAsk
            dfResult.loc[i, 'CoverType'] = thisOrder.coverCondition
            dfResult.loc[i, 'TargetBid'] = thisOrder.targetBid
            dfResult.loc[i, 'TargetAsk'] = thisOrder.targetAsk
            dfResult.loc[i, 'ExcuteBid'] = thisOrder.excuteBid
            dfResult.loc[i, 'ExcuteAsk'] = thisOrder.excuteAsk
            dfResult.loc[i, 'OOMPnl'] = thisOrder.OMMPnl
            dfResult.loc[i, 'Pnl'] = thisOrder.Pnl
            dfResult.loc[i, 'TriggerSL'] = thisOrder.triggerSL
            dfResult.loc[i, 'TriggerTTE'] = thisOrder.triggerTTE

        return dfResult

    def showOngoingSheet(self):
        """Show the sheet of ongoing order"""
        # show completed order
        if not self.orderOngoing:
            return None
        columns = [
            'recv_time', 'Side', 'MTBid', 'MTAsk', 'CoverType', 'TargetBid',
            'TargetAsk', 'ExcuteBid', 'ExcuteAsk', 'OOMPnl', 'Pnl',
            'TriggerSL', 'TriggerTTE'
        ]
        dfResult = pd.DataFrame(index=range(len(self.orderOngoing)),
                                columns=columns)
        for i in range(len(self.orderOngoing)):
            thisOrder = self.orderOngoing[i]
            dfResult.loc[i, 'recv_time'] = thisOrder.recv_time
            dfResult.loc[i, 'Side'] = thisOrder.direction
            dfResult.loc[i, 'MTBid'] = thisOrder.MTBid
            dfResult.loc[i, 'MTAsk'] = thisOrder.MTAsk
            dfResult.loc[i, 'CoverType'] = thisOrder.coverCondition
            dfResult.loc[i, 'TargetBid'] = thisOrder.targetBid
            dfResult.loc[i, 'TargetAsk'] = thisOrder.targetAsk
            dfResult.loc[i, 'ExcuteBid'] = thisOrder.excuteBid
            dfResult.loc[i, 'ExcuteAsk'] = thisOrder.excuteAsk
            dfResult.loc[i, 'OOMPnl'] = thisOrder.OMMPnl
            dfResult.loc[i, 'Pnl'] = thisOrder.Pnl
            dfResult.loc[i, 'TriggerSL'] = thisOrder.triggerSL
            dfResult.loc[i, 'TriggerTTE'] = thisOrder.triggerTTE

        return dfResult


class MktData:
    def __init__(self, Bid, Ask, tick):
        self.Bid = Bid
        self.Ask = Ask
        self.tick = tick


class Order:
    """"""
    def __init__(self, direction, recv_time, mktData):
        self.direction = direction
        self.recv_time = recv_time
        self.MTBid = mktData.Bid
        self.MTAsk = mktData.Ask
        self.excuteBid = None
        self.excuteAsk = None
        self.targetBid = None
        self.targetAsk = None
        self.MTmidPrice = (mktData.Bid + mktData.Ask) / 2
        self.MTPnl = (mktData.Bid - mktData.Ask) / 2
        # MTPnl is the Pnl if the order excute as mkt taker
        self.OMMPnl = None
        # OMMPnl is the Pnl from OMM
        self.Pnl = None
        # total Pnl = MTPnl + OMMPnl
        self.triggerSL = False
        self.triggerTTE = False
        self.coverCondition = None
        self.excu_time = None


@unique
class CoverType(Enum):
    MT = 0
    OMMSide = 1
    OMMMid = 2


@unique
class MarketType(Enum):
    NoType = 0
    MER = 1
    TrendUp = 2
    TrendDown = 3

    AlwaysMT = 100
    AlwaysOMMSide = 101
    AlwaysOMMid = 102


e = Excution(timeInterval, orderSet, priceSet)
e.backtest()

time.sleep(5)

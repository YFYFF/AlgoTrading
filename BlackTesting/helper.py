# -*- coding: utf-8 -*-
"""
Created on Tue Feb  4 13:18:05 2020

@author: WilliamNG
"""
"""
Algo_Trading HW1
note that the return is simple return 

"""
import os
import pandas as pd
import numpy as np
import scipy
import time
from scipy import stats
import matplotlib.pyplot as plt
from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()
import seaborn as sns


class Read():
    def __init__(self, path, col):
        """
        :param path: the path of the csv file
        :param col: which col we are reading, a list
        """
        self._path = path
        self._col = col
        self.df = pd.DataFrame()
    
    def read(self):
        df_temp = pd.read_csv(self._path, index_col='DateTime')
        df_temp.index = pd.to_datetime(df_temp.index)
        self._col.append('Price_Close')
        self.df = df_temp[self._col]
        
        #get return for the price
        price_lag = self.df['Price_Close'].shift(1)
        self.df.loc[:, 'Return_Close'] = self.df['Price_Close'] / price_lag - 1
        self.df = self.df.replace([np.inf, -np.inf], 0)
        self.df = self.df.fillna(value={'Return_Close':0})
        self.df = self.df.drop(['Price_Close'], axis=1)
        self.df = self.df.drop(['Return_Close'], axis=1)
    

        
class Performance():
    def __init__(self, df, rf=0, varnum=0.05):
        self.df = df
        self._rf = rf
        self._varnum = varnum
        
        #cummulative return (mutiple with each other)
        #data type: DataFrame
        self.cumReturn_df = (1+self.df).cumprod()
        self.days = len(self.df.index)
        
    
    @property
    def rf(self):
        return self._rf
    
    @property
    def varnum(self):
        return self._varnum
    
    @rf.setter
    def rf(self, riskfreerate):
        self._rf = riskfreerate
    
    @varnum.setter
    def varnum(self, var_number):
        self._varnum = var_number
    
    def maxDrawDown(self):
        cumReturn_df = self.cumReturn_df
        cumsum = cumReturn_df.cummax()
        dropnum = ((cumsum - cumReturn_df) / cumsum).max()
        self.maxDrawDown_num = dropnum.rename('maxDD')
        return self.maxDrawDown_num
    
    def sharpe(self):
        """
        Parameters
        ----------
        financialRate : float
            your rate of rinancing
        """
        self.sharpe_num = (self.cumReturn() - self._rf * self.days) / self.volatility()
        self.sharpe_num = self.sharpe_num.rename('Sharpe')
        return self.sharpe_num
    
    def cumReturn(self):
        self.cumReturn_num = (self.cumReturn_df .iloc[-1, :] - 1).rename('cumReturn')
        return self.cumReturn_num
    
    def volatility(self):
        self.volatility_num = self.df.std() * np.sqrt(self.days)
        self.volatility_num = self.volatility_num.rename('Volatility')
        return self.volatility_num
        
    def cumreturnToMaxDD(self):
        self.cumreturnToMaxDD_num = self.cumReturn() / self.maxDrawDown()
        self.cumreturnToMaxDD_num = self.cumreturnToMaxDD_num.rename('Return/MaxDD')
        return self.cumreturnToMaxDD_num

        
    def aveReturn(self):
        self.aveReturn_num = self.df.mean().rename('aveReturn')
        return self.aveReturn_num
    
    def getVaR(self):
        self.VaR = self.df.quantile(0.05, interpolation='lower').rename('VaR')
        return self.VaR
    
        
    def generatePerformance(self):
        a = self.maxDrawDown()
        b = self.volatility()
        c = self.cumReturn()
        d = self.cumreturnToMaxDD()
        e = self.aveReturn()
        f = self.sharpe()
        self.gendf = pd.concat([a, b, c, d, e, f], axis=1)
        return self.gendf

    
    def cumReturnPlot(self):
        #plt.figure()
        col = self.cumReturn_df.columns
        self.cumReturn_df[col].plot(grid=True, figsize=(15,7))
        plt.show()
    
    def performanceSheet(self):
        print(self.gendf)
        self.gendf.to_csv('result.csv')
    
    def performanceBar(self):
        #plt.figure()
        self.gendf.plot.bar(grid=True, subplots=True, figsize=(7, 15))
        self.gendf.plot.bar(grid=True, figsize=(15, 8))
        plt.show()
    
    def performanceDis(self):
        #plt.figure()
        self.df.plot(kind='kde', figsize=(15, 7))
        plt.show()
        
        

def main():
    path1 = './data/Assignment#1_Performance_track_records_Spring2020_out.csv'
    #col1 = ['03_02', '03_08', '03_09', '01_03', '01_08']
    # col1 = ['03_01', '03_02', '03_03', '03_04',
    #    '03_05', '03_06', '03_07', '03_08', '03_09', '03_10', '03_11', '03_12',
    #    '01_01', '01_02', '01_03', '01_04', '01_05', '01_06', '01_07', '01_08',
    #    '01_09', '01_10', '01_11', '01_12']
    col1 = ['03_03', '03_04', '01_02', '03_07', '01_09']
    read1 = Read(path1, col1)
    read1.read()

    per = Performance(read1.df)

    per.generatePerformance()
    per.performanceSheet()
    per.performanceDis()
    per.performanceBar()
    per.cumReturnPlot()
    
    print(per.getVaR())
    
if __name__ == '__main__':
    main()
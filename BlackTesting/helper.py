# -*- coding: utf-8 -*-
"""
Created on Tue Feb  4 13:18:05 2020

@author: WilliamNG
"""
"""
IAQF problem one helper
generate data of portfolio

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


from datetime import datetime, timedelta
def getClosestValue(dt, df):
    if type(dt) is str:
        dt = datetime.strptime(dt, '%Y-%m-%d')
    if dt in df.index:
        return df[dt]
    else: 
        dt = dt - timedelta(days=1)
        return getClosestValue(dt, df)


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
        self.cumreturnToMaxDD_num =  self.cumReturn() / self.maxDrawDown()
        self.cumreturnToMaxDD_num = self.cumreturnToMaxDD_num.rename('Return/MaxDD')
        return self.cumreturnToMaxDD_num
    
    def cumReturnPlot(self):
        col = self.cumReturn_df.columns
        self.cumReturn_df[col].plot(grid=True, figsize=(15,7))
        plt.show()
        
    def aveReturn(self):
        self.aveReturn_num = self.df.mean().rename('aveReturn')
        return self.aveReturn_num
    
    def getVaR(self):
        self.VaR = self.df.quantile(self._varnum, interpolation='lower').rename('VaR')
        return self.VaR
    
    
    def getCVaR(self):
        self.CVaR = self.df[self.df < self.getVaR()].mean().rename('CVaR')
        return self.CVaR
    



    def generatePerformance(self):
        a = self.maxDrawDown()
        b = self.volatility()
        c = self.cumReturn()
        d = self.cumreturnToMaxDD()
        e = self.aveReturn()
        f = self.sharpe()
        g = self.getVaR()
        h = self.getCVaR()
        
        self.gendf = pd.concat([a, b, c, d, e, f, g, h], axis=1)
        return self.gendf

    
    def performanceSheet(self):
        with pd.option_context('display.max_rows', None, 'display.max_columns', None):
            print(self.gendf)
    
    def performanceBar(self):
        self.gendf.plot.bar(grid=True, subplots=True, figsize=(7, 15))
        self.gendf.plot.bar(grid=True, figsize=(15, 8))
    
    def performanceDis(self):
        self.df.plot(kind='kde', figsize=(15, 7))



def timeseries(start_dt, end_dt, lasting_dt, df_return):
    from datetime import datetime
    t1 = time.time()
    """
    :传入 开始时间，结束时间，希望搞一次的工作日数e.g.5，整个原始数据
    :传出 一个含有所有东西的df
    """
    #generate a df have necessary infomation for create the loop
    # of Performance class
    a = df_return[start_dt:end_dt]['PORTFOLIO_r']
    b = df_return[start_dt:end_dt]['PORTFOLIO_d']
    c = df_return[start_dt:end_dt]['S&P500']
    df_useful = pd.concat([a, b, c], axis=1, names=['r', 'd', 'spx'])


    #get the list of dates we need
    #useful_idx_list = df_useful.index
    useful_index_list = [x.strftime('%Y-%m-%d') for x in df_useful.index]
    each_start_list = useful_index_list[0:-(lasting_dt-1)]
    each_end_list = useful_index_list[lasting_dt-1:]

    #get columns
    temp = Performance(df_useful.head())

    #get time series result
    columns = ['start', 'end', 'name', 'period']
    columns.extend(temp.generatePerformance().columns) #TODO: get self.gendf
    df_result = pd.DataFrame(index=range(len(each_end_list)*3), columns=columns)
    df_result['period'] = lasting_dt
    t2 = time.time()
    #generate each time's result
    for i in range(len(each_end_list)):
        each_start = each_start_list[i]
        
        each_end = each_end_list[i] #the next day of ending
        df_perTime = df_useful[each_start:each_end] #the time interval
        idx_in_result = int(3*i)

        temp =  Performance(df_perTime)
        temp_gendf = temp.generatePerformance()

        for num in range(3):
            df_result.loc[idx_in_result+num, temp_gendf.columns] = temp_gendf.iloc[num]
            df_result.loc[idx_in_result+num, 'name'] = temp_gendf.index[num]
            df_result.loc[idx_in_result+num, 'start'] = each_start
            df_result.loc[idx_in_result+num, 'end'] = each_end
    
    t3 = time.time()
    print(t2-t1)
    print(t3-t1)       
    return df_result











def main():
    pass

if __name__ == '__main__':
    main()    
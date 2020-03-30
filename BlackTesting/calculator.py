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


class Performance():
    def __init__(self, df, principal=1, rf=0, varnum=0.01):
        self.df = df
        self._rf = rf
        self._varnum = varnum
        self.principal = principal
        
        #cummulative return (mutiple with each other)
        #data type: DataFrame
        self.cumReturn_df = self.df.cumsum()
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
        dropnum = ((cumsum - cumReturn_df) / self.principal).max()
        self.maxDrawDown_num = dropnum.rename('maxDD')
        return self.maxDrawDown_num
    
    def yearlyReturn(self):
        self.yearlyReturn_num = self.cumReturn() * (252/self.days)
        self.yearlyReturn_num = self.yearlyReturn_num.rename('yearlyReturn')
        return self.yearlyReturn_num

    def sharpe(self):
        """
        #yearly sharp ratio
        """
        self.sharpe_num = (self.yearlyReturn() - self._rf * self.days) / self.volatility()
        self.sharpe_num = self.sharpe_num.rename('Sharpe')
        return self.sharpe_num
    
    def cumReturn(self):
        self.cumReturn_num = (self.cumReturn_df .iloc[-1, :]).rename('cumReturn')
        return self.cumReturn_num
    
    def volatility(self):
        self.volatility_num = self.df.std() * np.sqrt(252)
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
        g = self.yearlyReturn()
        h = self.getVaR()
        self.gendf = pd.concat([a, b, c, d, e, f, g, h], axis=1)
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
    pass
    
if __name__ == '__main__':
    main()
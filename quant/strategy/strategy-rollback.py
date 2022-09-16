from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import backtrader as bt
from backtrader import Order
import pandas as pd

dataUrl = 'D:\学习\区块链\\biandata\%s\%sUSDT-1m-%s.csv'
initCrash = 2500.0
# 倍数
crashMul = 20.0

def get_csv_kline(coin, date):
    columnList = ['data', 'Open', 'High', 'Low', 'Close', 'Volume', 'Close time', 'Quote asset volume',
                  'Number of trades', 'Taker buy base asset volume', 'Taker buy quote asset volume', 'Ignore']
    df = pd.read_csv(dataUrl % (coin, coin.upper(), date), names=columnList)
    df['data'] = pd.to_datetime(df['data'], unit='ms')
    df.set_index('data', inplace=True)
    # print(df)
    return df

sellPricePercent = 0.02
closePricePercent = 0.02
total_profit = 0.0
buyTime = 0
sellTime = 0
successTime = 0
total_buyTime = 0
total_sellTime = 0
total_successTime = 0

# Create a Stratey
class TestStrategy(bt.Strategy):
    lines = ('macd', 'signal', 'histo')
    params = (
        ('maperiod', 10),
        ('emaperiod', 1800),
        ('em1_period', 12),
        ('em2_period', 26),
        ('signal_period', 9),
        ('sellPricePercent', sellPricePercent),
        ('closePricePercent', closePricePercent),
    )

    def log(self, txt, dt=None):
        ''' Logging function fot this strategy'''
        print('%s, %s' % (self.datas[0].datetime.date(0).isoformat() + ' ' + self.datas[0].datetime.time().isoformat(), txt))

    def __init__(self):
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close
        self.datahigh = self.datas[0].high
        self.dataopen = self.datas[0].open
        self.datalow = self.datas[0].low

        # To keep track of pending orders and buy price/commission
        self.order = None
        self.buyprice = None
        self.buycomm = None

        self.macdlist = [0.0, 0.0, 0.0]
        self.rollHighlist = [0.0, 0.0, 0.0]

        # Add a MovingAverageSimple indicator
        # self.sma = bt.indicators.SimpleMovingAverage(
        #     self.datas[0], period=self.params.maperiod)
        self.ema = bt.indicators.EMA(self.data, period=self.params.emaperiod)

        self.macd = bt.indicators.MACD(self.data,
                                       period_me1=self.p.em1_period,
                                       period_me2=self.p.em2_period,
                                       period_signal=self.p.signal_period)

        self.rsi = bt.indicators.RSI_Safe(self.datas[0], period=6)
        self.rsi1 = bt.indicators.RSI_Safe(self.datas[0], period=12)
        self.rsi2 = bt.indicators.RSI_Safe(self.datas[0], period=24)

    def notify_order(self, order):
        global buyTime, sellTime, successTime
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    'BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                    (order.executed.price,
                     order.executed.value,
                     order.executed.comm))
                buyTime += 1

            else:  # Sell
                self.log(
                    'SELL EXECUTED, Price: %.4f, Cost: %.4f, Comm %.4f, macd: %.5f, signal: %.5f, histo: %.5f rsi: %.2f, ema: %.2f' %
                    (order.executed.price,
                     order.executed.value,
                     order.executed.comm,
                     self.macd.macd[0], self.macd.signal[0], self.macd.macd[0] - self.macd.signal[0], self.rsi[0],
                     self.ema[0]))
                sellTime += 1

            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        self.order = None

    def notify_trade(self, trade):
        global successTime
        if not trade.isclosed:
            return

        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f\n' %
                 (trade.pnl, trade.pnlcomm))
        if trade.pnl > 0.0:
            successTime += 1

    def next(self):
        # Simply log the closing price of the series from the reference
        # self.log('Close, %.2f' % self.dataclose[0])

        # Check if an order is pending ... if yes, we cannot send a 2nd one
        if self.order:
            return

        # Check if we are in the market
        if not self.position:

            # 可以购买
            if self.is_can_buy():
                # BUY, BUY, BUY!!! (with all possible default parameters)
                # self.log('BUY CREATE, %.2f' % self.dataclose[0])
                # Keep track of the created order to avoid a 2nd order
                size = int(initCrash * crashMul / self.dataclose[0])
                self.order = self.buy(size=size)
                self.log(
                    'SELL CREATE, macd: %.5f, signal: %.5f, histo: %.5f rsi: %.2f, %.2f, %.2f, ema: %.2f, macdlist: %s, rollHighlist: %s' %
                    (self.macd.macd[0], self.macd.signal[0], self.macd.macd[0] - self.macd.signal[0], self.rsi[0], self.rsi1[0], self.rsi2[0],
                     self.ema[0], self.macdlist, self.rollHighlist))

        else:

            if self.dataopen[0] <= self.ema:
                # 小于均线卖卖卖！
                # self.log('SELL CREATE, %.2f' % self.dataclose[0])

                # Keep track of the created order to avoid a 2nd order
                self.order = self.sell(exectype=Order.Limit, size=self.position.size)

    def is_can_buy(self):
        if self.ema > self.dataopen[0]:
            return True
        else:
            return False

def backt_strategy_run(coin, date):
    global buyTime, sellTime, successTime
    buyTime = 0
    sellTime = 0
    successTime = 0

    cerebro = bt.Cerebro()

    walletCash = 1000000
    cerebro.broker.setcash(walletCash)
    cerebro.addstrategy(TestStrategy)

    feed = bt.feeds.PandasData(dataname=get_csv_kline(coin, date))
    cerebro.adddata(feed)

    # Set the commission - 0.1% ... divide by 100 to remove the %
    cerebro.broker.setcommission(commission=0.0004)
    # Add a FixedSize sizer according to the stake 每次买卖的股数量
    cerebro.addsizer(bt.sizers.FixedSize, stake=200)

    cerebro.run()

    print('日期：%s' % date)
    print('本金：%.2fU' % walletCash)
    print('收入：%.2fU' % (cerebro.broker.getvalue() - walletCash))
    print("买次数：%d" % buyTime)
    print("卖次数：%d" % sellTime)
    print("成功次数：%d" % successTime)
    if buyTime != 0:
        print("成功率：%.2f%%" % (100.0 * successTime / buyTime))

    # print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
    global total_profit
    total_profit += (cerebro.broker.getvalue() - walletCash)
    print('总收益：%.2f' % total_profit)

    global total_buyTime, total_sellTime, total_successTime
    total_buyTime += buyTime
    total_sellTime += sellTime
    total_successTime += successTime

    # 打印图表
    # cerebro.plot()

if __name__ == '__main__':
    coin = 'eth'
    backt_strategy_run(coin, '2022-04')

    print('\n币：' + coin)
    print("总买次数：%d" % total_buyTime)
    print("总卖次数：%d" % total_sellTime)
    print("总成功次数：%d" % total_successTime)
    total_success_rate = 0.0
    if total_buyTime != 0:
        total_success_rate = (100.0 * total_successTime / total_buyTime)
        print('总成功率: %.2f%%' % total_success_rate)

    print("%s,%s,%s,%.2f,%d,%d,%.2f%%,%.4f,%.4f" % (
        coin,
        '2021-05-2022-04',
        '高成功率类型-high差值',
        total_profit,
        total_buyTime,
        total_successTime,
        total_success_rate,
        sellPricePercent,
        closePricePercent))

    # print result:
    # 日期：2022 - 04
    # 本金：1000000.00U
    # 收入：-54120.73U
    # 买次数：1132
    # 卖次数：1131
    # 成功次数：544
    # 成功率：48.06 %
    # 总收益：-54120.73
    #
    # 币：eth
    # 总买次数：1132
    # 总卖次数：1131
    # 总成功次数：544
    # 总成功率: 48.06 %
    # eth, 2021 - 05 - 2022 - 04, 高成功率类型 - high差值, -54120.73, 1132, 544, 48.06 %, 0.0200, 0.0200



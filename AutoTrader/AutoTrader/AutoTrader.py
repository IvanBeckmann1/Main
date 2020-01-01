'''
Created on Dec 22, 2019

@author: USER
'''

import json
from oandapyV20 import API
import oandapyV20.endpoints.orders as orders
from oandapyV20.exceptions import V20Error, StreamTerminated
from oandapyV20.endpoints.pricing import PricingStream
from requests.exceptions import ConnectionError
import logging
import argparse
from oandapyV20.contrib.factories import InstrumentsCandlesFactory
from datetime import datetime
from datetime import timedelta
import matplotlib.pyplot as plt 
import time
import pandas
from mpl_finance import candlestick_ohlc
import oandapyV20.endpoints.accounts as accounts
#from builtins import True, False

#SETTING OF ACCOUNT DETAILS
account_ID, auth_token = '101-004-12973613-001', '22a182dd493beaef1788331ce0cdcec9-d5bed0570c1ce0aae0e23cc705e70898'

def ConvertDate(Convert_Date):
    answer = str(Convert_Date.year)
    if Convert_Date.month < 10:
        answer = answer + "-0" + str(Convert_Date.month)
    else:
        answer = answer + "-" + str(Convert_Date.month)
    if Convert_Date.day < 10:
        answer = answer + "-0" + str(Convert_Date.day) + "T"
    else:
        answer = answer + "-" + str(Convert_Date.day) + "T"
    if Convert_Date.hour < 10:
        answer = answer + "0" + str(Convert_Date.hour)
    else:
        answer = answer + str(Convert_Date.hour)
    if Convert_Date.minute < 10:
        answer = answer + ":0" + str(Convert_Date.minute) + ":00Z"
    else:
        answer = answer + ":" + str(Convert_Date.minute) + ":00Z"
    return answer

def GetTradingSession(hour):
    
    #FUNCTION RETURNS A PRINT OF ANY ACTIVE TRADE SESSIONS
    
    current_trading_session = ""
    current_time = hour
    
    if (current_time >= 22) and (current_time <= 6):
        current_trading_session = current_trading_session + "[SYDNEY]"
    if (current_time >= 0) and (current_time <= 8):
        current_trading_session = current_trading_session + "[TOKYO]"
    if (current_time >= 8) and (current_time <= 16):
        current_trading_session = current_trading_session + "[LONDON]"
    if (current_time >= 13) and (current_time <= 21):
        current_trading_session = current_trading_session + "[NEW YORK]"
    
    print('')
    if current_trading_session == "":
        print("There are currently no active trading sessions.")
    else:
        print("Current active trading sessions: " + current_trading_session)

def GetOHLCData(account_ID, from_date, to_date, inst, freq):
    params = {"from": from_date, "to": to_date, "granularity": freq, "count":2500,}
    
    x_count = 0
    x_list = []
    o_list = []
    c_list = []
    h_list = []
    l_list = []
    time_list = []
    
    for r in InstrumentsCandlesFactory(instrument=inst,params=params):
        output_json = client.request(r)
        
        for a in output_json['candles']:
            x_count += 1
            open_pos = float(a['mid']['o'])
            close_pos = float(a['mid']['c'])
            high_pos = float(a['mid']['h'])
            low_pos = float(a['mid']['l'])
            time_list.append(x_count)
            x_list.append(a['time'])
            o_list.append(open_pos)
            c_list.append(close_pos)
            h_list.append(high_pos)
            l_list.append(low_pos)
    
    df = pandas.DataFrame(output_json['candles'])
    
    return time_list, x_list, o_list, c_list, h_list, l_list, df
    
def getSupportLevels(account_ID, from_date, to_date, inst, freq):
    
    #####################################################################
    #                        Pivot Point Calc                           #
    #https://www.babypips.com/learn/forex/how-to-calculate-pivot-points #
    #####################################################################
    
    time_list, x_list, o_list, c_list, h_list, l_list, df = GetOHLCData(account_ID, from_date, to_date, inst, freq)
    
    #Calculate OHLC of last trading session
    
    low_day = 9999
    high_day = 0
    open_day = c_list[0]
    close_day = c_list[len(c_list)-1]
    
    for k in range(len(c_list)):
        if l_list[k] < low_day:
            low_day = l_list[k]
        if h_list[k] > high_day:
            high_day = h_list[k]
    
    pp = (high_day + low_day + close_day) / 3
    
    support_1 = (2*pp) - high_day
    resistance_1 = (2 * pp) - low_day
    
    support_2 = pp - (high_day - low_day)
    resistance_2 = pp + (high_day - low_day)
    
    support_3 = low_day - (2 * (high_day - pp))
    resistance_3 = high_day + (2 * (pp - low_day))
    
    return support_1, support_2, support_3, resistance_1, resistance_2, resistance_3

def ShowCandleChart(account_ID, from_date, to_date, inst, freq, show_support, show_trend):
    time_list, x_list, o_list, c_list, h_list, l_list, df = GetOHLCData(account_ID, from_date, to_date, inst, freq)
    df['o'] = o_list
    df['h'] = h_list
    df['l'] = l_list
    df['c'] = c_list
    df['dates'] = time_list
    plt.style.use('ggplot')
    ohlc = df.loc[:,['dates', 'o', 'h', 'l', 'c']]
    
    S1, S2, S3, R1, R2, R3 = getSupportLevels(account_ID, c_db_yesterday, c_yesterday, pair, 'M1')
    
    fig, ax = plt.subplots()
    candlestick_ohlc(ax, ohlc.values, width = 0.6, colorup='white', colordown='black', alpha=0.8)
    
    ax.set_xlabel('Date')
    ax.set_ylabel('Price')
    fig.suptitle('Hourly Candlestick Chart')
    
    if show_support == True:
        df['S1'] = S1
        df['S2'] = S2
        df['S3'] = S3
        df['R1'] = R1
        df['R2'] = R2
        df['R3'] = R3
        
        ax.plot(df['dates'], df['S1'], color='green', label='S1')
        ax.plot(df['dates'], df['S2'], color='green', label='S2')
        ax.plot(df['dates'], df['S3'], color='green', label='S3')
        
        ax.plot(df['dates'], df['R1'], color='red', label='R1')
        ax.plot(df['dates'], df['R2'], color='red', label='R2')
        ax.plot(df['dates'], df['R3'], color='red', label='R3')
        
        plt.legend()
    
    if show_trend == True:
        lower_range, upper_range = GetTrend(account_ID, c_start, c_end, pair, freq)
        df['Trend Upper Range'] = upper_range
        df['Trend Lower Range'] = lower_range
        
        ax.plot(df['dates'], df['Trend Upper Range'], color='green', label='Trend - upper range')
        ax.plot(df['dates'], df['Trend Lower Range'], color='green', label='Trend - lower range')
        
        #plt.legend()
        
    fig.tight_layout()
    plt.show()
    
def CheckPassed(list_of_y, c, slope):
    answer = True
    for s in range(len(list_of_y)):
        if answer == True:
            if ((slope * (s+1) + c)) < list_of_y[s]:
                answer = False
    return answer

def GetTrend(accountID, from_date, to_date, inst, freq):
    time_list, x_list, o_list, c_list, h_list, l_list, df = GetOHLCData(account_ID, from_date, to_date, inst, freq)
    slope, c, x_1, x_2 = 0.0, 0.0, 0.0, 0.0
    
    x_1 = 1
    x_2 = len(x_list)
    
    #FIRST DUMMY CALC
    slope = (h_list[x_2 - 1] - h_list[x_1 - 1]) / (x_2 - x_1)
    c = h_list[x_2 - 1] - (slope * x_2)
    
    #SENSE CHECK TO MAKE SURE TWO POINTS DON'T DOMINATE THE LINE
    #If the range used covers less than half the population then we can't say for certain...
    #If we have an at least 50% population coverage between the two points it should be fine
    x_range = x_2 - x_1
    ratio = x_range / len(h_list) 
       
    while CheckPassed(h_list, c, slope) == False or ratio < 0.5:
        if x_2 > (1):
            x_2 -= 1
        else:
            x_2 = len(h_list) 
            x_1 += 1
        try:
            slope = (h_list[x_2 - 1] - h_list[x_1 - 1]) / (x_2 - x_1)
        except:
            slope = 0
        c = h_list[x_2 - 1] - (slope * x_2)
        x_range = x_2 - x_1
        ratio = x_range / len(h_list)
        #Add in values to recalc entire list in equation terms
        #print(slope)
        
    #C above represents top range, now we just calculate the bottom range using C2 as our bottom indicator
    
    c2 = c
    for z in range(len(l_list)):
        if l_list[z] < ((slope * (z+1) + c2)):
            c2 -= (((slope * (z+1) + c2)) - l_list[z])
    print(c-c2)
    
    print(x_1)
    print(x_2)
    
    trading_range = (abs(c-c2))
    
    lower_limit = ((slope * (z+1)) + c2) + 0.2 * trading_range
    upper_limit = ((slope * (z+1)) + c) - 0.2 * trading_range
    

    if ratio > 0.5:
        if slope > 0:
            print("Overall positive trend between " + from_date + " and " + to_date)
        if slope < 0:
            print("Overall negative trend between " + from_date + " and " + to_date)
        if slope == 0:
            print("Sideways trend between " + from_date + " and " + to_date)
        print("Trading range is around " + str(trading_range * 10000) + " pips.")
        if c_list[z] <= lower_limit:
            print("We are currently within the bottom 20% of the range, this might be a good time to buy")
        if c_list[z] >= upper_limit:
            print("We are currently within the top 20% of the range, this might be a good time to sell")
        
    else:
        print("Range covered with line is too short to conclude on trend. Use visuals for reference")
    
    upper_range = []
    lower_range = []
    
    for k in range(len(h_list)):
        upper_range.append((slope*(k+1))+c)
        lower_range.append((slope*(k+1))+c2)
    
    return lower_range, upper_range

def FindCandlestickPattern (account_ID, from_date, to_date, inst, freq):
    #This script identifies a series of Japenese Candlestick patterns that can be found at
    #https://www.babypips.com/learn/forex/lone-rangers-single-candlestick-patterns
    
    time_list, x_list, o_list, c_list, h_list, l_list, df = GetOHLCData(account_ID, from_date, to_date, inst, freq)
    
    #Recognizing Hammers
    #Long Shadow / Body > (2-3)
    #Upper Shadow < 15%
    #Follow on at least 4 downwards patterns in past 5 movements
    #Confirmed by at least 1 positive movement post indicator
    #Stores as a hammer on the upwards confirmation tick
    hammer_list = []
    for k in range(len(c_list)):
        hammer_list.append(False)
        if k > 4:
            #Test for at least 4 downwards movements in past 5 movements
            downwards_count = 0
            for m in range(5):
                if c_list[k-(m+1)] < o_list[k-(m+1)]:
                    downwards_count += 1
            if downwards_count >= 4:
                #Test for shadow length
                shadow_length = min(o_list[k], c_list[k]) - l_list[k]
                body_length = abs(o_list[k] - c_list[k])
                upper_shadow = h_list[k] - max(o_list[k], c_list[k])
                trading_range = h_list[k] - l_list[k]
                if (shadow_length > (body_length * 3)) and ((upper_shadow / trading_range) < 0.15):
                    if (k + 1) < len(c_list):
                        if c_list[k+(1)] > o_list[k+(1)]:
                            print("Potential hammer identified at: " + str(k + 1))
                            hammer_list[k] = True
                
    #Recognizing Hanging Man
    #Long Shadow / Body > (2-3)
    #Upper Shadow < 15%
    #Follow on at least 4 upwards patterns in past 5 movements
    #Confirmed by at least 1 negative movement post indicator
    #Stores as a hanging man on the downwwards confirmation tick
    
    hanging_list = []
    for k in range(len(c_list)):
        hanging_list.append(False)
        if k > 4:
            #Test for at least 4 downwards movements in past 5 movements
            downwards_count = 0
            for m in range(5):
                if c_list[k-(m+1)] > o_list[k-(m+1)]:
                    downwards_count += 1
            if downwards_count >= 4:
                #Test for shadow length
                shadow_length = min(o_list[k], c_list[k]) - l_list[k]
                body_length = abs(o_list[k] - c_list[k])
                upper_shadow = h_list[k] - max(o_list[k], c_list[k])
                trading_range = h_list[k] - l_list[k]
                if (shadow_length > (body_length * 3)) and ((upper_shadow / trading_range) < 0.15):
                    if (k + 1) < len(c_list):
                        if c_list[k+(1)] < o_list[k+(1)]:
                            print("Potential hanging man identified at: " + str(k + 1))    
                            hanging_list[k] = True    
    
    #Recognizing Inverted Hammer
    #Long Shadow / Body > (2-3)
    #Lower Shadow < 15%
    #Follow on at least 4 downwards patterns in past 5 movements
    #Confirmed by at least 1 positive movement post indicator
    #Stores as a inverted hammer on the positive confirmation tick
    
    inverted_hammer_list = []
    for k in range(len(c_list)):
        inverted_hammer_list.append(False)
        if k > 4:
            #Test for at least 4 downwards movements in past 5 movements
            downwards_count = 0
            for m in range(5):
                if c_list[k-(m+1)] < o_list[k-(m+1)]:
                    downwards_count += 1
            if downwards_count >= 4:
                #Test for shadow length
                shadow_length = min(o_list[k], c_list[k]) - l_list[k]
                body_length = abs(o_list[k] - c_list[k])
                upper_shadow = h_list[k] - max(o_list[k], c_list[k])
                trading_range = h_list[k] - l_list[k]
                if (upper_shadow > (body_length * 3)) and ((shadow_length / trading_range) < 0.15):
                    if (k + 1) < len(c_list):
                        if c_list[k+(1)] > o_list[k+(1)]:
                            print("Potential inverted hammer identified at: " + str(k + 1))    
                            inverted_hammer_list[k] = True   
    
    #Recognizing Shooting Star
    #Long Shadow / Body > (2-3)
    #Lower Shadow < 15%
    #Follow on at least 4 upward patterns in past 5 movements
    #Confirmed by at least 1 negative movement post indicator
    #Stores as a Shooting Star on the negative confirmation tick
    
    shooting_star_list = []
    for k in range(len(c_list)):
        shooting_star_list.append(False)
        if k > 4:
            #Test for at least 4 downwards movements in past 5 movements
            downwards_count = 0
            for m in range(5):
                if c_list[k-(m+1)] > o_list[k-(m+1)]:
                    downwards_count += 1
            if downwards_count >= 4:
                #Test for shadow length
                shadow_length = min(o_list[k], c_list[k]) - l_list[k]
                body_length = abs(o_list[k] - c_list[k])
                upper_shadow = h_list[k] - max(o_list[k], c_list[k])
                trading_range = h_list[k] - l_list[k]
                if (upper_shadow > (body_length * 3)) and ((shadow_length / trading_range) < 0.15):
                    if (k + 1) < len(c_list):
                        if c_list[k+(1)] < o_list[k+(1)]:
                            print("Potential shooting star identified at: " + str(k + 1))    
                            shooting_star_list[k] = True  
                            
    #Recognizing Bullish Engulfing
    #Pls fix def
    
    bullish_engulfing_list = []
    for k in range(len(c_list)):
        bullish_engulfing_list.append(False)
        if k > 4:
            #Test for at least 4 downwards movements in past 5 movements
            downwards_count = 0
            for m in range(5):
                if c_list[k-(m+2)] < o_list[k-(m+2)]:
                    downwards_count += 1
            if downwards_count >= 4:
                #Test for shadow length
                if c_list[k-1] < o_list[k-1]:
                    if c_list[k] > o_list[k-1]:
                        if (k + 1) < len(c_list):
                            if c_list[k+(1)] > o_list[k+(1)]:
                                print("Potential bullish engulfing identified at: " + str(k + 1))    
                                bullish_engulfing_list[k] = True  
    #Recognizing Bullish Engulfing
    #Pls fix def
    
    bearish_engulfing_list = []
    for k in range(len(c_list)):
        bearish_engulfing_list.append(False)
        if k > 4:
            #Test for at least 4 downwards movements in past 5 movements
            downwards_count = 0
            for m in range(5):
                if c_list[k-(m+2)] > o_list[k-(m+2)]:
                    downwards_count += 1
            if downwards_count >= 4:
                #Test for shadow length
                if c_list[k-1] > o_list[k-1]:
                    if c_list[k] < o_list[k-1]:
                        if (k + 1) < len(c_list):
                            if c_list[k+(1)] < o_list[k+(1)]:
                                print("Potential bearish engulfing identified at: " + str(k + 1))    
                                bearish_engulfing_list[k] = True 
    
    #Recognizing Tweezer Bottoms
    #Pls fix def
    
    tweezer_bottoms_list = []
    for k in range(len(c_list)):
        tweezer_bottoms_list.append(False)
        if k > 4:
            #Test for at least 4 downwards movements in past 5 movements
            downwards_count = 0
            for m in range(5):
                if c_list[k-(m+2)] < o_list[k-(m+2)]:
                    downwards_count += 1
            if downwards_count >= 4:
                shadow_length = min(o_list[k-1], c_list[k-1]) - l_list[k-1]
                body_length = abs(o_list[k-1] - c_list[k-1])
                upper_shadow = h_list[k-1] - max(o_list[k-1], c_list[k-1])
                trading_range = h_list[k-1] - l_list[k-1]
                if (shadow_length > (body_length * 3)) and ((upper_shadow / trading_range) < 0.15) and (c_list[k-1] < o_list[k-1]):
                    shadow_length_2 = shadow_length
                    shadow_length = min(o_list[k], c_list[k]) - l_list[k]
                    body_length = abs(o_list[k] - c_list[k])
                    upper_shadow = h_list[k] - max(o_list[k], c_list[k])
                    trading_range = h_list[k] - l_list[k]
                    if (shadow_length > (body_length * 3)) and ((upper_shadow / trading_range) < 0.15) and (c_list[k] > o_list[k]):
                        if ((shadow_length_2 >= shadow_length * 0.90) or (shadow_length_2 <= shadow_length / 0.90)):
                            if ((l_list[k-1] >= l_list[k] * 0.90) or (l_list[k-1] <= l_list[k]/ 0.90)):
                                if c_list[k+(1)] > o_list[k+(1)]:
                                    print("Potential tweezer bottoms identified at: " + str(k + 1))    
                                    tweezer_bottoms_list[k] = True 
                                    
    #Recognizing Tweezer Tops
    #Pls fix def
    
    tweezer_tops_list = []
    for k in range(len(c_list)):
        tweezer_tops_list.append(False)
        if k > 4:
            #Test for at least 4 downwards movements in past 5 movements
            downwards_count = 0
            for m in range(5):
                if c_list[k-(m+2)] > o_list[k-(m+2)]:
                    downwards_count += 1
            if downwards_count >= 4:
                shadow_length = min(o_list[k-1], c_list[k-1]) - l_list[k-1]
                body_length = abs(o_list[k-1] - c_list[k-1])
                upper_shadow = h_list[k-1] - max(o_list[k-1], c_list[k-1])
                trading_range = h_list[k-1] - l_list[k-1]
                if (upper_shadow > (body_length * 3)) and ((shadow_length / trading_range) < 0.15) and (c_list[k-1] > o_list[k-1]):
                    shadow_length_2 = upper_shadow
                    shadow_length = min(o_list[k], c_list[k]) - l_list[k]
                    body_length = abs(o_list[k] - c_list[k])
                    upper_shadow = h_list[k] - max(o_list[k], c_list[k])
                    trading_range = h_list[k] - l_list[k]
                    if (upper_shadow > (body_length * 3)) and ((shadow_length / trading_range) < 0.15) and (c_list[k] < o_list[k]):
                        if ((shadow_length_2 >= upper_shadow * 0.90) or (shadow_length_2 <= upper_shadow / 0.90)):
                            if ((h_list[k-1] >= h_list[k] * 0.90) or (h_list[k-1] <= h_list[k]/ 0.90)):
                                if c_list[k+(1)] < o_list[k+(1)]:
                                    print("Potential tweezer tops identified at: " + str(k + 1))    
                                    tweezer_tops_list[k] = True 
    
    #Recognizing Evening Star
    #Pls fix def
    
    tweezer_tops_list = []
    for k in range(len(c_list)):
        tweezer_tops_list.append(False)
        if k > 4:
            #Test for at least 4 downwards movements in past 5 movements
            downwards_count = 0
            for m in range(5):
                if c_list[k-(m+3)] < o_list[k-(m+3)]:
                    downwards_count += 1
            if downwards_count >= 4:
                shadow_length = min(o_list[k-2], c_list[k-2]) - l_list[k-2]
                body_length = abs(o_list[k-2] - c_list[k-2])
                upper_shadow = h_list[k-2] - max(o_list[k-2], c_list[k-2])
                trading_range = h_list[k-2] - l_list[k-2]
                if (c_list[k-2] < o_list[k-2]):
                    shadow_length_2 = upper_shadow
                    shadow_length = min(o_list[k], c_list[k]) - l_list[k]
                    body_length = abs(o_list[k] - c_list[k])
                    upper_shadow = h_list[k] - max(o_list[k], c_list[k])
                    trading_range = h_list[k] - l_list[k]
                    if (upper_shadow > (body_length * 3)) and ((shadow_length / trading_range) < 0.15) and (c_list[k] < o_list[k]):
                        if ((shadow_length_2 >= upper_shadow * 0.90) or (shadow_length_2 <= upper_shadow / 0.90)):
                            if ((h_list[k-1] >= h_list[k] * 0.90) or (h_list[k-1] <= h_list[k]/ 0.90)):
                                if c_list[k+(1)] < o_list[k+(1)]:
                                    print("Potential tweezer tops identified at: " + str(k + 1))    
                                    tweezer_tops_list[k] = True 
    
    return hammer_list, hanging_list, inverted_hammer_list, shooting_star_list, bullish_engulfing_list, bearish_engulfing_list, tweezer_bottoms_list, tweezer_tops_list

print("------------------------------")
print("WElCOME TO IVAN'S FOREX TRADER")
print("------------------------------")

print("Which trading pair are you looking at today?")
print("[1]GBP_USD")
print("[2]EUR_USD")

trading_pair = input("Enter option: ")

if trading_pair == "1":
    pair = "GBP_USD"
elif trading_pair == "2":
    pair = "EUR_USD"
else:
    print("No valid trading pair entered, defaulting to GBP_USD.")
    pair = "GBP_USD"
print("")

print("-----------------------------")
print("What do you want to do?")
print("[1] Market Analysis")
print("[2] Account Details")
print("[3] Open Trades")

option = input("Enter option: ")

if option == "1":
    
    look_ahead = 3

    #Pull in trading session information
    GetTradingSession(datetime.now().hour)
    
    #Small delay so that the session info is actually displayed
    time.sleep(1)
    
    #A status update print
    print("")
    print("-------------")
    print("Loading values...")
    print("-------------")
    print("")
    
    #Loads the client - doing it here because it is used in multiple functions
    client = API(access_token = auth_token)
    
    #Initialize all variables used for technical analysis
    end = datetime.now()
    start = end - timedelta(days = 1)
    
    far_start = end - timedelta(days = 120)
    far_end = end - timedelta(days = 0)
    #Pulls in current range (now and 7 days prior) and converts this into an acceptable format for OANDA
    
    yesterday = end - timedelta(days = 1)
    db_yesterday = yesterday - timedelta(days = 1)
    
    answer = str(yesterday.year)
    if yesterday.month < 10:
        answer = answer + "-0" + str(yesterday.month)
    else:
        answer = answer + "-" + str(yesterday.month)
    if yesterday.day < 10:
        answer = answer + "-0" + str(yesterday.day) + "T"
    else:
        answer = answer + "-" + str(yesterday.day) + "T"
    
    answer = answer + "23:00:00Z"
    
    c_yesterday = answer
    
    answer = str(db_yesterday.year)
    if db_yesterday.month < 10:
        answer = answer + "-0" + str(db_yesterday.month)
    else:
        answer = answer + "-" + str(db_yesterday.month)
    if db_yesterday.day < 10:
        answer = answer + "-0" + str(db_yesterday.day) + "T"
    else:
        answer = answer + "-" + str(db_yesterday.day) + "T"
    
    answer = answer + "23:00:00Z"
        
    c_db_yesterday = answer
    
    print(c_yesterday)
    print(c_db_yesterday)
    
    c_end = ConvertDate(end)
    c_start = ConvertDate(start)
    c_far_start = ConvertDate(far_start)
    c_far_end = ConvertDate(far_end)
    

    S1, S2, S3, R1, R2, R3 = getSupportLevels(account_ID, c_db_yesterday, c_yesterday, pair, 'M1')
    
    print("Past resistance levels.")
    GetTrend(account_ID, c_start, c_end, pair, 'M15')
    
    print("Past trend")
    hammer_list, hanging_list, inverted_hammer_list, shooting_star_list, bullish_engulfing_list, bearish_engulfing_list, tweezer_bottoms_list, tweezer_tops_list = FindCandlestickPattern(account_ID, c_far_start, c_far_end, pair, 'M15')

    print("Past Candlesticks")
    for k in range(len(hammer_list)):
        output_text = ""
        if hammer_list[k] == True:
            output_text = output_text + "[HAMMER]"
        if hanging_list[k] == True:
            output_text = output_text + "[HANGING MAN]"
        if inverted_hammer_list[k] == True:
            output_text = output_text + "[INVERTED HAMMER LIST]"
        if shooting_star_list[k] == True:
            output_text = output_text + "[SHOOTING STAR]"
        if bullish_engulfing_list[k] == True:
            output_text = output_text + "[BULLISH ENGULFING]"
        if bearish_engulfing_list[k] == True:
            output_text = output_text + "[BEARISH ENGULFING]"
        if tweezer_bottoms_list[k] == True:
            output_text = output_text + "[TWEEZER BOTTOMS]"
        if tweezer_tops_list[k] == True:
            output_text = output_text + "[TWEEZER TOPS]"
        if output_text != "":
            print(str(k+1) + ": " + output_text)
    
    time_list, x_list, o_list, c_list, h_list, l_list, df = GetOHLCData(account_ID, c_far_start, c_far_end, pair, 'M15')
    
    hammer, hanging_man, inverted_hammer, shooting_star, bullish_engulfing, bearish_engulfing, tweezer_bottoms, tweezer_tops = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
    
    for k in range(len(c_list)):
        if (k < len(c_list) - look_ahead):
            if hammer_list[k]==True:
                hammer -= (((c_list[k+1] - c_list[k+look_ahead]) * 10000) * (0.0001 / c_list[k+1])) * 100000
            if hanging_list[k]==True:
                hanging_man += (((c_list[k+1] - c_list[k+look_ahead]) * 10000) * (0.0001 / c_list[k+1])) * 100000
            if inverted_hammer_list[k]==True:
                inverted_hammer -= (((c_list[k+1] - c_list[k+look_ahead]) * 10000) * (0.0001 / c_list[k+1])) * 100000
            if shooting_star_list[k]==True:
                shooting_star += (((c_list[k+1] - c_list[k+look_ahead]) * 10000) * (0.0001 / c_list[k+1])) * 100000
            if bullish_engulfing_list[k]==True:
                bullish_engulfing -= (((c_list[k+1] - c_list[k+look_ahead]) * 10000) * (0.0001 / c_list[k+1])) * 100000
            if bearish_engulfing_list[k]==True:
                bearish_engulfing += (((c_list[k+1] - c_list[k+look_ahead]) * 10000) * (0.0001 / c_list[k+1])) * 100000
            if tweezer_bottoms_list[k]==True:
                tweezer_bottoms -= (((c_list[k+1] - c_list[k+look_ahead]) * 10000) * (0.0001 / c_list[k+1])) * 100000
            if tweezer_tops_list[k]==True:
                tweezer_tops += (((c_list[k+1] - c_list[k+look_ahead]) * 10000) * (0.0001 / c_list[k+1])) * 100000
    
    print("TRADING RESULTS FOR CANDLESTICK SIGNALS")
    print("---------------------------------------")
    print("Hammer: " + str(hammer))
    print("Hanging Man: " + str(hanging_man))
    print("Inverted Hammer: " + str(inverted_hammer))
    print("Shooting Star: " + str(shooting_star))
    print("Bullish Engulfing: " + str(bullish_engulfing))
    print("Bearish Engulfing: " + str(bearish_engulfing))
    print("Tweezer Tops: " + str(tweezer_tops))
    print("Tweezer Bottoms: " + str(tweezer_bottoms))
    print("---------------------------------------")
    
    ShowCandleChart(account_ID, c_start, c_end, pair, 'M15', True, True)
    
if option == "2":
    
    client = API(access_token = auth_token)
    account_balance = accounts.AccountSummary(account_ID)
    
    client.request(account_balance)
    respon = account_balance.response
    
    print('')
    print('------------------------')
    print('--' + respon['account']['id'] + "--")
    print('------------------------')
    
    print(respon)
    print('Balance: ' + respon['account']['currency'] + " " + respon['account']['balance'])
    print('Margin Leverage: ' + str(int(1/float(respon['account']['marginRate']))) + ":1")
    print('Unrealised P&L on open positions: ' + respon['account']['currency'] + " " + respon['account']['unrealizedPL'])
    print('Realised P&L on closed positions: ' + respon['account']['currency'] + " " + respon['account']['pl'])
    print('Margin Used: ' + respon['account']['currency'] + " " + respon['account']['marginUsed'])
    print('Margin Available: ' + respon['account']['currency'] + " " + respon['account']['marginAvailable'])
    
'''

orderConf = [
       # ok
       {
         "order": {
            "units": "100",
            "instrument": "EUR_USD",
            "timeInForce": "FOK",
            "type": "MARKET",
            "positionFill": "DEFAULT"
          }
        }
       # wrong instrument, gives an error
]
api = API(access_token = '22a182dd493beaef1788331ce0cdcec9-d5bed0570c1ce0aae0e23cc705e70898')

for O in orderConf:
    r = orders.OrderCreate(accountID='101-004-12973613-001', data=O)
    print("processing : {}".format(r))
    print("===============================")
    print(r.data)
    try:
        response = api.request(r)
    except V20Error as e:
        print("V20Error: {}".format(e))
    else:
        print("Response: {}\n{}".format(r.status_code, json.dumps(response, indent=2)))
print('success')

'''

#101-004-12973613-001
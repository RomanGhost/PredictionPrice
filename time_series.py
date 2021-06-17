import re
import yfinance as yf
from sklearn import preprocessing
import joblib
from datetime import datetime as dt
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime as dt
import time

import os
os.environ['TF_MIN_LOG_LEVEL'] = "2"
import tensorflow as tf
from tensorflow.keras.models import load_model
import telebot

API_TOKEN = # 'BOT TOKEN HERE'
bot = telebot.TeleBot(API_TOKEN, parse_mode=None) 

text = "I will send you prediction Nintendo stock once a day\nUnsubscribe- /end"

def write_id(list_id, id_int):
    mean = len(list_id)//2
    minimum = 0
    maximum = len(list_id)-1
    
    while list_id[mean] != id_int and minimum<=maximum:
        if id_int < list_id[mean]:
            maximum = mean-1
        else:
            minimum = mean+1
        mean = (minimum+maximum)//2
    return mean

def add_element(list_ids, new_id):
    num = write_id(list_ids, new_id)
    return list_ids[:num+1] + [new_id] + list_ids[num+1:]

def del_element(list_ids, del_id):
    num = write_id(list_ids, del_id)
    return list_ids[:num] + list_ids[num+1:]

def min_max_date(month, day):
    return [(month-1)/11, day/4]

model = load_model('/home/ghost/actions/time_series_gru')
print('model is done')
min_max_price = joblib.load('price_norm.joblib')

def send_actions():
    if os.path.isfile('id.txt'):
        file = open('id.txt', 'r', encoding='utf8')
        ids = file.readlines()
        file.close()
        
    ntdoy = yf.Ticker('NTDOY')
    old  =  ntdoy.history(period = '3mo',
                      interval='1d')
    days_p = 45
    inp_data = old[['Close']][len(old)-days_p:].to_dict()["Close"]
    new_data = []

    for i in inp_data:
        date = re.findall(r'\d{4}-\d{2}-\d{2}', str(i))[0]
        date_int = map(int, date.split('-'))
        day = dt(*date_int).weekday()
        month = int(date.split('-')[1])

        price = min_max_price.transform([[inp_data[i]]])[0][0]
        month, day = min_max_date(month, day)

        new_data.append([month, day, price])
    new_data = np.array([new_data], dtype=np.float32)
        
    predict = model.predict(new_data)
    predict = round(min_max_price.inverse_transform(predict)[0, 0], 3)
    
    now = dt.now()
    text_price = 'prediction price on {}-{}-{}(y-m-d) = {}$'
    if now.weekday() < 4:
        return text_price.format(now.year, now.month, now.day + 1, predict)
    else:
        return text_price.format(now.year, now.month, now.day + 2, predict)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, 'Hi!\n'+text)
    
    if os.path.isfile('id.txt'):
        file = open('id.txt', 'r', encoding='utf8')
        ids = file.readlines()
        file.close()
        if str(message.chat.id)+'\n' not in ids:
            file = open('id.txt', 'w', encoding='utf8')
            new_ids = add_element(list(map(int, ids)), message.chat.id)
            
            for i in new_ids:
                file.write(str(i)+'\n')
            file.close()
    else:
        file = open('id.txt', 'w', encoding='utf8')
        file.write(str(message.chat.id))#message.chat.id
        file.close()
  
@bot.message_handler(commands=['end'])
def send_welcome(message):
    bot.send_message(message.chat.id, 'Ok, bye')
    
    if os.path.isfile('id.txt'):
        file = open('id.txt', 'r', encoding='utf8')
        ids = file.readlines()
        file.close()

        if str(message.chat.id) not in ids:
            file = open('id.txt', 'w', encoding='utf8')
            new_ids = del_element(list(map(int, ids)), message.chat.id)
            
            for i in new_ids:
                file.write(str(i)+'\n')
            file.close()
    
@bot.message_handler(commands=['send_action_price'])
def send_welcome(message):
    bot.send_message(message.chat.id, send_actions())
    
@bot.message_handler(commands=['help'])
def send_welcome(message):
    bot.send_message(message.chat.id, text)
    
@bot.message_handler(func=lambda m: True)
def echo_all(message):
    bot.send_message(message.chat.id, message.text)
    
send_act = True
now = dt.now()
if now.weekday() < 4 and now.time().hour == 18 and send_act:
    file = open('id.txt', 'r', encoding='utf8')
    ids = file.readlines()
    file.close()
    text_act = send_actions()
    for i in ids[1:]:
        bot.send_message(int(i), text_act)

if now.weekday() < 4 and \
now.time().hour == 1 and \
(now.time().min > 1 and now.time().min < 3) and \
send_act:
    send_act = False
      
bot.polling()
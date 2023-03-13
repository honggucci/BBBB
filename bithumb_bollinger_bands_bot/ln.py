import telegram
import asyncio

from pybithumb import Bithumb
import pandas as pd
import time
from datetime import datetime 
from pytz import timezone
import traceback

bithumb = Bithumb()  # 본인 아이디

now=datetime.now(timezone('Asia/Seoul')).strftime('%Y-%m-%d %H:%M:%S')
# ======================

#       라인링크

names = ['LN']

# ======================

# 평균매수가 저장 TXT
txt_pass = './ln.txt'
# 이 가격이상가면 전량매도
num = 100000.0 

def data_h(typee = '',hours=''):
    data=bithumb.get_candlestick(typee,chart_intervals=hours)['close'].to_frame()
    data.columns=['price']
    
    # 볼린저 밴드 25 2.5
    data['MA_25'] = data['price'].rolling(window=25,min_periods=1).mean()
    data['MA_100'] = data['price'].rolling(window=100,min_periods=1).mean()
    data['SD'] = data['price'].rolling(window=25,min_periods=1).std()
    data['UP_B'] = data['MA_25'] + (data['SD'] * 2.5 )
    data['LOW_B'] =  data['MA_25'] - (data['SD'] * 2.5 )
    
    return data.bfill()


def buyy(typee = '',target_price = 0 ,countt = 0):

    buy_unit = float(bithumb.get_balance(typee)[0])
    buy_legacy = bithumb.buy_market_order(typee,countt)

    time.sleep(5)
    my_buy_price = bithumb.get_order_completed(buy_legacy)['data']['contract'][0]['price']
    my_buy_unit = bithumb.get_order_completed(buy_legacy)['data']['contract'][0]['units']
    average_price = ((float(fx * buy_unit) + (float(my_buy_price)) * float(my_buy_unit))  / (buy_unit+ float(my_buy_unit)))

    with open(txt_pass, 'w+') as f:
        f.write(str(round(average_price,5)))

    return my_buy_price ,my_buy_unit ,average_price ,buy_unit


def selll(typee = '',target_price = 0 ,countt = 0):
    
    sell_unit = float(bithumb.get_balance(typee)[0])
    sell_legacy = bithumb.sell_market_order(typee,countt)

    
    time.sleep(5)
    my_sell_price = bithumb.get_order_completed(sell_legacy)['data']['contract'][0]['price']
    my_sell_unit = bithumb.get_order_completed(sell_legacy)['data']['contract'][0]['units']
    # average_price_1 = ((float(fx * buy_unit) + (float(my_buy_price)) * float(my_buy_unit))  / (buy_unit+ float(my_buy_unit)))
    # with open(txt_pass, 'w+') as f:
    #    f.write(str(average_price_1))
    
    return my_sell_price ,my_sell_unit ,sell_unit


def tele(xv=''):
    try :
        if len(xv) != 0 :
            async def main():
                bot = telegram.Bot(token='') # 자기꺼
                chat_id =  '' # 자기꺼
                await bot.sendMessage(chat_id, xv)

            asyncio.run(main())
        
        else :
            pass
    except Exception as e:
        with open('./tele_error.txt','a') as log:
            log.writelines(now +' : ' + traceback.format_exc() + ' \n')
        pass

def now_price1(s=''):
    return bithumb.get_current_price(s)
    

while (True):
    try: 
        buy_lines=''
        sell_lines=''
        for name in names:
            with open(txt_pass, 'r') as f:
                fx = f.read()
                fx = round(float(fx),5)       
                
            # 현재가격
            now_price = float(now_price1(name))
            if now_price > num:
                # 걸어논거 전부 취소하고 시장가 매도
                end_game = bithumb.get_balance(name)[0]
                bithumb.buy_market_order(name,end_game)
                print('전부 청산')
                break

            data_6h=data_h(name,'5m')
            data_1h=data_h(name,'1m')

            target_price_up_6h = float(data_6h['UP_B'][-1])
            target_price_up_6h = round(target_price_up_6h,5)
            target_price_dw_6h = float(data_6h['LOW_B'][-1])
            target_price_dw_6h = round(target_price_dw_6h,5)

            target_price_up_1h = float(data_1h['UP_B'][-1])
            target_price_up_1h = round(target_price_up_1h,5)
            target_price_dw_1h = float(data_1h['LOW_B'][-1])
            target_price_dw_1h = round(target_price_dw_1h,5)
            
            # 1000원치 매수할 시 수량 , 시장가 주문
            count = round((1000/ now_price),5)
            counx = float(bithumb.get_balance(name)[0])
            #with open("./log.txt", "a") as log:
                #log.writelines('==============================/n')
            try :

                if data_6h['MA_25'][-1] >= data_6h['MA_100'][-1]: # 상승장
                    if target_price_dw_1h >= now_price :
                    # 10 분 볼린저 밴드 하단에 맞춰 매수 가격 주문 / 무조건 채널에 걸리면 매수 
                        my_buy_price ,my_buy_unit ,average_price ,buy_unit = buyy(name,target_price_dw_1h,count)
                        print(my_buy_price + ' 에 샀다 / 상승장')
                        with open("./log.txt", "a") as log:
                            log.writelines(now + ' :  ' + name+'_buyprice : ' + str(my_buy_price) + ' , count : ' + str(my_buy_unit) + ' average : ' + str(round(average_price,1)) + ' UP \n')
                        with open('./log.txt','r') as x:
                            buy_lines = x.readlines()[-1]
                        tele(buy_lines)
                    else :
                        print('안삼 / 상승장')
                        # with open("./log.txt", "a") as log:
                            # log.writelines(now + ' : 안삼 / 상승장 /n')
                    # 1 시간 볼린저 밴드 상단에 맞춰 매도 가격 주문 
                    # 전체에 1/5만 매도 주문 
                    # 만약 내 평단이 상단 채널 가격보다 적다면 매도 안함
                    if target_price_up_6h <= now_price :
                        if float(fx) * 1.1  <= now_price:
                            my_sell_price ,my_sell_unit ,sell_unit = selll(name,target_price_dw_1h,round((counx/10),5))
                            print(my_sell_unit + ' 판매 성공 / 상승장')
                            with open("./log.txt", "a") as log:
                                log.writelines(now + ' :  ' + name+'_sellprice : ' + str(my_sell_price) + ' , count : ' + str(my_sell_unit) + ' average : ' + str(round(fx,1)) + ' UP \n')
                            with open('./log.txt','r') as y:
                                sell_lines = y.readlines()[-1]
                            tele(sell_lines)

                        else : 
                            print('평단가보다 낮다 , 안팜 / 상승장 /n')
                            # with open("./log.txt", "a") as log:
                                # log.writelines(now + ' : 평단가보다 낮다 , 안팜 / 상승장 /n')
                            pass

                    else :
                        print('안팜 / 볼밴 상단에 터치 못함 / 상승장')
                        # with open('./log.txt','a') as log:
                            # log.writelines(now + ' : 안팜 / 볼밴 상단에 터치 못함 / 상승장 /n')
                        pass

                elif data_6h['MA_25'][-1] < data_6h['MA_100'][-1]: # 하락장
                    
                    if target_price_dw_6h >= now_price : 
                    # 1 시간 볼린저 밴드 하단에 맞춰 매수 가격 주문 / 무조건 채널에 걸리면 매수
                        my_buy_price ,my_buy_unit, average_price ,all_unit = buyy(name,target_price_dw_1h,count) 
                        print(my_buy_price + ' 산다 / 하락장')
                        with open('./log.txt','a') as log:
                            log.writelines(now + ' :  ' + name+'_buyprice : ' + str(my_buy_price) + ' , count : ' + str(my_buy_unit) + ' average : ' + str(round(average_price,1)) + ' DOWN \n')
                        with open('./log.txt','r') as x:
                            buy_lines = x.readlines()[-1]
                        tele(buy_lines)
                    else :
                        print('안삼 / 하락장')   
                        # with open('./log.txt','a') as log:
                            # log.writelines(now + ' : 안삼 / 하락장 /n')
                    # 10 분 볼린저 밴드 상단에 맞춰 매도 가격 주문 
                    # 전체에 1/5만 매도 주문 
                    # 만약 내 평단이 상단 채널 가격보다 적다면 매도 안함

                    if target_price_up_1h <= now_price : 
                        if (float(fx)) *1.1 <= now_price :
                            my_sell_price ,my_sell_unit ,sell_unit = selll(name,target_price_dw_1h,round((counx/5),5))
                            print(my_sell_price + ' 판매 성공 / 하락장')
                            with open('./log.txt','a') as log:
                                log.writelines(now + ' :  ' + name+'_sellprice : ' + str(my_sell_price) + ' , count : ' + str(my_sell_unit) + ' average : ' + str(round(fx,1)) + ' DOWN \n')
                            with open('./log.txt','r') as y:
                                sell_lines = y.readlines()[-1]
                            tele(sell_lines)
                                # ('ask', 'XRP', 'C0106000000493141030', 'KRW')

                        else :
                            print('평단가보다 낮음 / 하락장')
                            # with open('./log.txt','a') as log:
                                # log.writelines(now + ' : 평단가보다 낮음 / 하락장 /n')
                            pass
                    else :
                        print('안팜 / 볼밴 상단에 터치 못함 / 하락장 ')
                        # with open('./log.txt','a') as log:
                        #     log.writelines(now + ' : 안팜 / 볼밴 상단에 터치 못함 / 하락장 /n')
                        pass
                else :
                    pass
            except:
                pass
        print('성공 후 대기 중')
        time.sleep(60)


    except Exception as e :
        with open('./log.txt','a') as log:
            log.writelines(now +' : ' + traceback.format_exc())
        print('실패 후 대기 중')
        break
        

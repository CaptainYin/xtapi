import random
import numpy as np
import matplotlib.pyplot as plt
from xt_api import SignedRequestAPI
from xt_utils import get_auth_payload
from xt_api import PublicRequestAPI
pb = PublicRequestAPI()
accesskey = '9f94baf4-b87b-498c-8457-2f888ad58c23'
secretkey = '30e22600e25c5b04034b396d12ace15fcecf56ad'
sra = SignedRequestAPI(accesskey, secretkey)
price_Point=4
coin_Point=4
gap_precent=0.001
price_scale=0.2
symbol='xrp_usdt'

def get_random(a,b):
    return random.random()*(b-a)+a
def Mysample(func,a,b,c,size):
# a,b,c, is the Monte Carlo range for x,y
# must cover func
# defaut func>0
    cout=0
    res=[]
    while cout<size:
        print(a,b,c,size,cout)
        x=get_random(a,b)
        print('x:',x)
        y=get_random(0,c)
        print('y:',y)
        if(func(x)>y):
            print('func(x):',func(x))
            cout+=1
            res.append(x)
    return res

def p(a):
    return (1+a*(a**2+1)**(-0.5) )/(a+np.sqrt(a**2+1))
def gen_price1(p,last_price=1.2,gap_precent=0.001,price_scale=0.2,bid_size=100,ask_size=100):
    data=Mysample(p,0,10,1.1,ask_size)
    amin=last_price*(1+gap_precent)
    amax=last_price*(1+price_scale)
    ask_price=np.array(data)/10*(amax-amin)+amin
    
    data=Mysample(p,-10,0,1.1,bid_size)
    amax=last_price*(1-gap_precent)
    amin=last_price*(1-price_scale)
    bid_price=np.array(data)/10*(amax-amin)+amax
    return ask_price,bid_price
def p1(a,last_price):
    amin=last_price*(1+gap_precent)
    amax=last_price*(1+price_scale)
    return p((a-amin)/(amax-amin)*10)
def p2(a,last_price):
    bmax=last_price*(1-gap_precent)
    bmin=last_price*(1-price_scale)
    return p((a-bmax)/(bmax-bmin)*10)
def P_diff1(x):
    return p2(x,last_price1)
def P_diff(x):
    a=last_price1*(1+gap_precent)
    b=last_price*(1+price_scale)
    c=last_price1*(1+price_scale)
    if a>b:
        return p1(x,last_price1)
    if x>=a and x<=b:
        return p1(x,last_price1)-p1(x,last_price)
    if x>b and x<=c:
        return p1(x,last_price1)
    return 0
def P_diff2(x):
    return p1(x,last_price1)
def P_diff4(x):
    if bmax1<bmin:
        return p1(x,last_price1)
    if x>=bmin and x<=bmax1:
        return p1(x,last_price1)-p1(x,last_price)
    if x<=bmin:
        return p1(x,last_price1)
    return 0
def cancel_by_prob(p):
    if random.random()<p:
        return True
    return False
def update_boundary(last_price):
    amin=last_price*(1+gap_precent)
    amax=last_price*(1+price_scale)
    bmax=last_price*(1-gap_precent)
    bmin=last_price*(1-price_scale)
    return amin,amax,bmax,bmin

def update_priceup(last_price,last_price1,old_ask_price,old_bid_price,bid_order_num,ask_order_num):
    amin,amax,bmax,bmin=update_boundary(last_price)
    amin1,amax1,bmax1,bmin1=update_boundary(last_price1)
    # deal ask_price
    #先撤单
    cancel_ask_price=[i for i in old_ask_price if i <= amin1]
    #撤多少补多少
    add_ask_price= Mysample(P_diff,amin1,amax1,1,len(cancel_ask_price))
    new_ask_price=[i for i in old_ask_price if i > amin1]
    new_ask_price.extend(add_ask_price)

    # deal bid_price
    #先按比率撤单
    cancel_bid_price=[]
    for i in old_bid_price:
        if i<bmax and i>bmin1:
            prob=(p2(i,last_price)-p2(i,last_price1))/p2(i,last_price)
            if cancel_by_prob(prob):
                cancel_bid_price.append(i)
        else:
            cancel_bid_price.append(i)
    new_bid_price=[]
    new_bid_price.extend(old_bid_price)
    for i in cancel_bid_price: new_bid_price.remove(i)
    #撤多少补多少
    add_bid_price= Mysample(P_diff1,max(bmax,bmin1),bmax1,1,bid_order_num-len(new_bid_price))
    new_bid_price.extend(add_bid_price)
    return new_bid_price,new_ask_price,cancel_bid_price,cancel_ask_price,add_bid_price,add_ask_price

def update_pricedown(last_price,last_price1,old_ask_price,old_bid_price,bid_order_num,ask_order_num):
    amin,amax,bmax,bmin=update_boundary(last_price)
    amin1,amax1,bmax1,bmin1=update_boundary(last_price1)
    cancel_ask_price=[]
    for i in old_ask_price:
        if i<amax1:
            prob=(p2(i,last_price)-p2(i,last_price1))/p2(i,last_price)
            if cancel_by_prob(prob):
                cancel_ask_price.append(i)
        else:
            cancel_ask_price.append(i)
    new_ask_price=[]
    new_ask_price.extend(old_ask_price)
    for i in cancel_ask_price: new_ask_price.remove(i)
    #撤多少补多少
    add_ask_price= Mysample(P_diff2,amin1,min(amin,amax1),1,ask_order_num-len(new_ask_price))
    new_ask_price.extend(add_ask_price)

    # deal bid_price
    #先撤单
    cancel_bid_price=[i for i in old_bid_price if i >= bmax1]
    #撤多少补多少
    add_bid_price= Mysample(P_diff4,bmin1,bmax1,1,len(cancel_bid_price))
    new_bid_price=[i for i in old_bid_price if i < bmax1]
    new_bid_price.extend(add_bid_price)
    return new_bid_price,new_ask_price,cancel_bid_price,cancel_ask_price,add_bid_price,add_ask_price
def update_pricechange(last_price,last_price1,old_ask_price,old_bid_price,bid_order_num,ask_order_num): 
    if last_price1>last_price:
        return update_priceup(last_price=last_price,last_price1=last_price1,old_ask_price=
                              old_ask_price,old_bid_price=old_bid_price,
                              bid_order_num=bid_order_num,ask_order_num=ask_order_num)
    else:
        return update_pricedown(last_price=last_price,last_price1=last_price1,old_ask_price=
                                old_ask_price,old_bid_price=old_bid_price,
                                bid_order_num=bid_order_num,ask_order_num=ask_order_num)
def place_orders(symbol,data):
    if len(data)<=100:
        kws=get_auth_payload({'market':symbol,'data':data})
        status,orders,_=sra.palce_orders(kwargs=kws)
    else:
        for i in range(len(data)//100):
            kws=get_auth_payload({'market':symbol,'data':data[i*100:(1+i)*100]})
            status,orders,_=sra.palce_orders(kwargs=kws)            
        if(len(data)%100!=0):
            kws=get_auth_payload({'market':symbol,'data':data[i*100:(1+i)*100]})
            status,orders,_=sra.palce_orders(kwargs=kws)  
            
def init_order(last_price,bid_size,ask_size): 
    ask_price,bid_price=gen_price1(p=p,last_price=last_price,gap_precent=0.001,price_scale=0.2,
                                   bid_size=bid_size,ask_size=ask_size)
    price=[round(x,price_Point) for x in bid_price]#买单
    data=[{'price':i,'amount':round(np.random.random()+10,coin_Point),'type':1} for i in price]
    price=[round(x,price_Point) for x in ask_price]#卖单
    data1=[{'price':i,'amount':round(np.random.random()+10,coin_Point),'type':0} for i in price]
    data.extend(data1)
    place_orders(symbol=symbol,data=data)


def divide_order(orders=[]):
    orders=orders['data']
    ask_orders=[]
    bid_orders=[]
    for iorder in orders:
        if iorder['type']==0:
            ask_orders.append(iorder)
        if iorder['type']==1:
            bid_orders.append(iorder)
    return ask_orders,bid_orders
def get_unfinished_order():
    #查询最新挂单
    kws=get_auth_payload({'market':symbol,'page':1,'pageSize':200 })
    status,orders,_=sra.get_unfinished_order(kwargs=kws)
    return divide_order(orders=orders)
    
def update_price(last_price,last_price1):
    #根据价格下相同价格相同数量的买卖单
    amount=round(np.random.random()+100000*abs(last_price1-last_price)/last_price,coin_Point)
    data=[{'price':last_price1,'amount':amount,'type':0},
        {'price':last_price1,'amount':amount,'type':1}]
    kws=get_auth_payload({'market':symbol,'data':data})
    status,orders,_=sra.palce_orders(kwargs=kws)
        
# def update_depth(bid_orders=[],ask_orders=[],last_price=1.0):
#     sample_ratio=0.5
#     # 查询ask，bid挂单
#     ask_orders,bid_orders=get_unfinished_order()
#     #从order产生orderid
#     bid_orderids=[]
#     for iorder in bid_orders:
#         bid_orderids.append(iorder['id'])
#     ask_orderids=[]
#     for iorder in ask_orders:
#         ask_orderids.append(iorder['id'])
#     #撤销价格变化必须撤销的挂单
#     bids_cancel_orderid=[]
#     asks_cancel_orderid=[]
#     for iorder in bid_orders:
#         if float(iorder['price'])>=last_price:
#             bids_cancel_orderid.append(iorder['id'])
#             bid_orders.remove(iorder)
#     for iorder in ask_orders:
#         if float(iorder['price'])<=last_price:
#             asks_cancel_orderid.append(iorder['id'])
#             ask_orders.remove(iorder)
#     #剩下单子里面随机更新
#     bids_sample_num = int(len(bid_orders)*sample_ratio)
#     bids_cancel_order=random.sample(bid_orders, bids_sample_num)
#     for i in bids_cancel_order:
#         bids_cancel_orderid.append(i['id'])
#     asks_sample_num = int(len(ask_orders)*sample_ratio)
#     asks_cancel_order=random.sample(ask_orders, asks_sample_num)
#     for i in asks_cancel_order:
#         asks_cancel_orderid.append(i['id'])
 
#     bids_cancel_orderid.extend(asks_cancel_orderid)
#     cancel_orderid=bids_cancel_orderid
#     # 撤销部分单子
#     kws=get_auth_payload({'market':symbol,'data':cancel_orderid})
#     status,orders,_=sra.cancel_orders(kwargs=kws)
    
#     # 查询ask，bid挂单
#     ask_orders,bid_orders=get_unfinished_order()
#     # 补上相应数量的单子
#     ask_price,bid_price=gen_price1(p=p,last_price=last_price,gap_precent=0.001,price_scale=0.2,bid_size=50-len(bid_orders),ask_size=50-len(ask_orders))

#     price=[round(x,price_Point) for x in bid_price]#买单
#     data=[{'price':i,'amount':round(np.random.random()+1,coin_Point),'type':1} for i in price]

#     price=[round(x,price_Point) for x in ask_price]#卖单
#     data1=[{'price':i,'amount':round(np.random.random()+1,coin_Point),'type':0} for i in price]
#     data.extend(data1)
#     kws=get_auth_payload({'market':symbol,'data':data})
#     status,orders,_=sra.palce_orders(kwargs=kws)
    
#     # 更新k线
#     update_price(last_price=last_price)
#     return bid_orders,ask_orders,last_price

def get_orderid_by_price(price,order):            
    cancel_orderid=[]
    for pri in price:
        for x in order:
            if float(x['price'])==pri:
                cancel_orderid.append(x['id'])
                break 
    return cancel_orderid    
#挂上初始买卖单###########################
status,data,_=pb.get_ticker(kwargs={'market':symbol})
last_price=data['price']    
init_order(last_price,150,150)
###########################    
status,data,_=pb.get_ticker(kwargs={'market':symbol})
last_price=data['price']


while True:
    #价格变化
    last_price1=round(last_price*(np.random.standard_normal(size=1)[0]/1000+1),price_Point)
    
    # status,data,_=pb.get_ticker(kwargs={'market':symbol})
    # last_price1=data['price']

    amin,amax,bmax,bmin=update_boundary(last_price)
    amin1,amax1,bmax1,bmin1=update_boundary(last_price1)
    #查询未完成订单
    kws=get_auth_payload({'market':symbol,'page':1,'pageSize':1000 })
    status,orders,_=sra.get_unfinished_order(kwargs=kws)
    ask_orders,bid_orders=divide_order(orders=orders)

    #提取价格
    old_ask_price=[float(x['price']) for x in ask_orders]
    old_bid_price=[float(x['price']) for x in bid_orders]

    new_bid_price,new_ask_price,cancel_bid_price,cancel_ask_price,add_bid_price,add_ask_price=update_pricechange(
        last_price=last_price,last_price1=last_price1,old_ask_price=old_ask_price,old_bid_price=old_bid_price,
        bid_order_num=150,ask_order_num=150)
    print('挂单数量:',len(ask_orders)+len(bid_orders),'撤单数量：',len(cancel_bid_price)+len(cancel_ask_price),
        '新挂单数量：',len(add_ask_price)+len(add_bid_price))
    #查询id
    cancel_orderid=get_orderid_by_price(price=cancel_ask_price,order=ask_orders)
    cancel_orderid.extend(get_orderid_by_price(price=cancel_bid_price,order=bid_orders))   
    # 撤单
    kws=get_auth_payload({'market':symbol,'data':cancel_orderid})
    status,orders,_=sra.cancel_orders(kwargs=kws)

    # 补单
    price=[round(x,price_Point) for x in add_bid_price]#买单
    data=[{'price':i,'amount':round(np.random.random()+10,coin_Point),'type':1} for i in price]
    price=[round(x,price_Point) for x in add_ask_price]#卖单
    data1=[{'price':i,'amount':round(np.random.random()+10,coin_Point),'type':0} for i in price]
    data.extend(data1)
    place_orders(symbol=symbol,data=data)

    # 更新k线
    update_price(last_price=last_price,last_price1=last_price1)
    last_price=last_price1
    print(last_price)





import random
from xt_api import SignedRequestAPI
from xt_utils import get_auth_payload
from xt_api import PublicRequestAPI

import numpy as np

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

def gen_price(last_price=1.2,gap_precent=0.001,price_scale=0.2,bid_size=100,ask_size=100):
    Y=np.sinh(10)
    y_max=Y*price_scale
    y_min=Y*gap_precent
    a_max=np.arcsinh(y_max)
    a_min=np.arcsinh(y_min)

    a=np.random.uniform(a_min,a_max,size=[ask_size])
    # print(np.sinh(a),Y,last_price)
    ask_price=np.sinh(a)/Y*last_price+last_price

    a=np.random.uniform(-a_max,-a_min,size=[bid_size])
    bid_price=np.sinh(a)/Y*last_price+last_price
    
    return ask_price,bid_price

# plt.hist(bid_price,100)

# plt.plot(a,y)

# ask_max=last_price*(1+price_scale)
# ask_min=last_price*(1+gap_precent)
# bid_max=last_price*(1-gap_precent)
# bid_min=last_price*(1-price_scale)

# print(len(a))
# ask_price=list(filter(lambda x:x>10*gap_precent/2,a))
# ask_price=list(filter(lambda x:x>y_max*gap_precent/2 and x<y_max*price_scale,y))
# ask_price=(np.array(ask_price)/y_max+1)*last_price
# bid_price=list(filter(lambda x:x<-y_max*gap_precent/2 and x>-y_max*price_scale,y))
# bid_price=(np.array(bid_price)/y_max+1)*last_price

# _=plt.hist(bid_price,100)
# _=plt.hist(ask_price,100)

pb = PublicRequestAPI()
accesskey = '9f94baf4-b87b-498c-8457-2f888ad58c23'
secretkey = '30e22600e25c5b04034b396d12ace15fcecf56ad'
sra = SignedRequestAPI(accesskey, secretkey)
price_Point=4
coin_Point=4
symbol='xrp_usdt'

#挂上初始买卖单###########################
status,data,_=pb.get_ticker(kwargs={'market':symbol})
last_price=data['price']
ask_price,bid_price=gen_price(last_price=last_price,gap_precent=0.001,price_scale=0.2,bid_size=50,ask_size=50)

price=[round(x,price_Point) for x in bid_price]#买单
data=[{'price':i,'amount':round(np.random.random()+1,coin_Point),'type':1} for i in price]

price=[round(x,price_Point) for x in ask_price]#卖单
data1=[{'price':i,'amount':round(np.random.random()+1,coin_Point),'type':0} for i in price]
data.extend(data1)

kws=get_auth_payload({'market':symbol,'data':data})
status,orders,_=sra.palce_orders(kwargs=kws)

ask_orders,bid_orders=divide_order(orders=orders)
###########################

sample_ratio=0.5
def get_unfinished_order():
    #查询最新挂单
    kws=get_auth_payload({'market':symbol,'page':1,'pageSize':200 })
    status,orders,_=sra.get_unfinished_order(kwargs=kws)
    return divide_order(orders=orders)
    
def update_price(last_price):
    #根据价格下相同价格相同数量的买卖单
    amount=round(np.random.random()+1,coin_Point)
    data=[{'price':last_price,'amount':amount,'type':0},
        {'price':last_price,'amount':amount,'type':1}]
    kws=get_auth_payload({'market':symbol,'data':data})
    status,orders,_=sra.palce_orders(kwargs=kws)
        
def update_depth(bid_orders=[],ask_orders=[],last_price=1.0):
    # 查询ask，bid挂单
    ask_orders,bid_orders=get_unfinished_order()
    #从order产生orderid
    bid_orderids=[]
    for iorder in bid_orders:
        bid_orderids.append(iorder['id'])
    ask_orderids=[]
    for iorder in ask_orders:
        ask_orderids.append(iorder['id'])
        
    
    #撤销价格变化必须撤销的挂单
    bids_cancel_orderid=[]
    asks_cancel_orderid=[]
    for iorder in bid_orders:
        if float(iorder['price'])>=last_price:
            bids_cancel_orderid.append(iorder['id'])
            bid_orders.remove(iorder)
    for iorder in ask_orders:
        if float(iorder['price'])<=last_price:
            asks_cancel_orderid.append(iorder['id'])
            ask_orders.remove(iorder)
    #剩下单子里面随机更新
    bids_sample_num = int(len(bid_orders)*sample_ratio)
    bids_cancel_order=random.sample(bid_orders, bids_sample_num)
    for i in bids_cancel_order:
        bids_cancel_orderid.append(i['id'])
    asks_sample_num = int(len(ask_orders)*sample_ratio)
    asks_cancel_order=random.sample(ask_orders, asks_sample_num)
    for i in asks_cancel_order:
        asks_cancel_orderid.append(i['id'])
 
 
    bids_cancel_orderid.extend(asks_cancel_orderid)
    cancel_orderid=bids_cancel_orderid
    # 撤销部分单子
    kws=get_auth_payload({'market':symbol,'data':cancel_orderid})
    status,orders,_=sra.cancel_orders(kwargs=kws)
    
    # 查询ask，bid挂单
    ask_orders,bid_orders=get_unfinished_order()
    # 补上相应数量的单子
    ask_price,bid_price=gen_price(last_price=last_price,gap_precent=0.001,price_scale=0.2,bid_size=50-len(bid_orders),ask_size=50-len(ask_orders))

    price=[round(x,price_Point) for x in bid_price]#买单
    data=[{'price':i,'amount':round(np.random.random()+1,coin_Point),'type':1} for i in price]

    price=[round(x,price_Point) for x in ask_price]#卖单
    data1=[{'price':i,'amount':round(np.random.random()+1,coin_Point),'type':0} for i in price]
    data.extend(data1)
    kws=get_auth_payload({'market':symbol,'data':data})
    status,orders,_=sra.palce_orders(kwargs=kws)
    
    # 更新k线
    update_price(last_price=last_price)
    
    return bid_orders,ask_orders,last_price
    
count=0

status,data,_=pb.get_ticker(kwargs={'market':symbol})
last_price=data['price']

while count!=1000000000:
    count=count+1
    print(count)
    # 生成随机价格
    last_price=round(last_price*(np.random.standard_normal(size=1)[0]/1000+1),price_Point)

    bid_orders,ask_orders,last_price=update_depth(bid_orders=bid_orders,ask_orders=ask_orders,last_price=last_price)
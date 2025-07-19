import os
import time
import json
import asyncio
import traceback
import websockets
from dotenv import load_dotenv
from api.Public_api import PublicAPI
from api.Auth_api import AuthAPI
from api.utils import sign


use_proxy = True
if use_proxy == True:
    proxy = 'http://127.0.0.1:7890'
else:
    proxy = None

# 初始化Backpack API客户端
load_dotenv()
api_key = os.getenv('API_KEY')
api_secret = os.getenv('API_SECRET')
public_api_client = PublicAPI(proxy=proxy)
auth_api_client = AuthAPI(api_key=api_key, api_secret=api_secret, proxy=proxy)
ws_url = 'wss://ws.backpack.exchange'

# 配置参数
initialBuyQuantity=0.01
buyIncrement=0.0
initialSellQuantity=0.01
sellIncrement=0.0
priceStep = 0.5
baseAsset = 'SOL'
quoteAsset = 'USDC'
numOrders = 3
dryRun = False
marketType = 'SPOT'
if marketType == 'SPOT':
    pair_name = baseAsset + '_' + quoteAsset
elif marketType == 'PERP':
    pair_name = baseAsset + '_' + quoteAsset + '_PERP'
else:
    raise ValueError('Invalid market type. It should be SPOT or PERP.')
marketInfo = public_api_client.get_market(pair_name)
if marketInfo['orderBookState'] != 'Open':
    raise ValueError('Invalid trade pair.')
unitPrice = float(marketInfo['filters']['price']['tickSize'])
unitQuantity = float(marketInfo['filters']['quantity']['stepSize'])
if unitPrice > priceStep:
    raise ValueError(f'Grid price step should be greater than the minimum price: {unitPrice}.')
for each in [initialBuyQuantity, buyIncrement, initialSellQuantity, sellIncrement]:
    if (each > 0) and (each < unitQuantity):
        raise ValueError(f'All quantity related params should be greater the minimum quantity: {unitQuantity}.')

# 初始化Telegram Bot
# bot_token = os.getenv('BOT_TOKEN')
# chat_id = os.getenv('CHAT_ID')
# bot = telegram.Bot(bot_token)
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

# 辅助变量
grid_orders = []  # 记录程序挂的单，防止手动订单干扰程序执行
trade_side_trans = {'Bid': 'BUY', 'Ask': 'SELL'}

def send_message(message):
    '''
    发送信息到Telegram
    '''
    print(message)  # 输出到日志
    # if not dryRun:
    #     loop.run_until_complete(bot.send_message(chat_id=chat_id, text=message))

def format_decimal(raw_number, unit_size):
    """将价格/数量格式化为符合标准的小数位数"""
    return float(raw_number) // float(unit_size) * float(unit_size)

def get_balance():
    """获取资产余额"""
    balance = {}
    raw_collaterals = auth_api_client.get_collaterals()['collateral']
    collaterals = {}
    for each in raw_collaterals:
        symbol = each['symbol']
        collaterals[symbol] = float(each['lendQuantity'])
    balances = auth_api_client.get_balances()
    for each in [baseAsset, quoteAsset]:
        balance[each] = {'free': float(balances[each]['available']), 'locked': float(balances[each]['locked'])}
        if each in collaterals.keys():
            balance[each]['free'] += collaterals[each]
    return balance

def get_signature():
    ts_ms = str(int((time.time())*1000))
    str_to_sign = f'instruction=subscribe&timestamp={ts_ms}&window=5000'
    signature = sign(str_to_sign, api_secret)
    signature_list = [api_key, signature, ts_ms, "5000"]
    return signature_list

def place_order(side, price, quantity):
    """挂单函数"""
    try:
        order = auth_api_client.place_order(
            symbol=pair_name,
            side=side,
            orderType='Limit',
            price=format_decimal(price, unitPrice),
            quantity=format_decimal(quantity, unitQuantity),
            timeInForce='GTC'
        )
        return order
    except Exception as e:
        send_message(f"挂单失败!\n{str(e)}\n{traceback.format_exc()}")
        return None

def update_orders(last_trade_side, last_trade_qty, last_trade_price):
    """检查并更新买卖挂单，保持每侧 3 个挂单"""

    # 清空挂单记录
    grid_orders.clear()

    # 取消当前挂单
    open_orders = auth_api_client.get_open_orders(symbol=pair_name, marketType=marketType)
    while open_orders:
        auth_api_client.cancel_open_orders(symbol=pair_name)
        time.sleep(1)
        open_orders = auth_api_client.get_open_orders(symbol=pair_name, marketType=marketType)

    # 获取余额
    if marketType == 'SPOT':
        balance = get_balance()
        base_balance = (balance[baseAsset]['free'] + balance[baseAsset]['locked']) if baseAsset in balance.keys() else 0
        quote_balance = balance[quoteAsset]['free'] + balance[quoteAsset]['locked'] if quoteAsset in balance.keys() else 0
    else:
        collaterals = auth_api_client.get_collaterals()
        free_equity = float(collaterals['netEquityAvailable'])
        leverage_factor = float(collaterals['imf'])

    # 确认起始买卖数量
    if last_trade_side == 'Bid':
        initial_buy_qty = last_trade_qty + buyIncrement
        initial_sell_qty = initialSellQuantity
    else:
        initial_buy_qty = initialBuyQuantity
        initial_sell_qty = last_trade_qty + sellIncrement

    # 买单：往下挂 priceStep 整数倍的价格
    for i in range(numOrders):
        buy_price = format_decimal((last_trade_price - (i + 1) * priceStep), unitPrice)
        buy_qty = format_decimal((initial_buy_qty + i * buyIncrement), unitQuantity)
        if marketType == 'SPOT':
            if quote_balance < buy_price * buy_qty:
                send_message(f"{quoteAsset}余额: {quote_balance}，无法在{buy_price}买入{buy_qty}{baseAsset}")
                break
        else:
            if free_equity < (buy_price * buy_qty * leverage_factor):
                send_message(f"保证金余额: {free_equity}USD，无法在{buy_price}做多{buy_qty}{baseAsset}")
                break
        if dryRun:
            print(f'在{buy_price}买入/做多{buy_qty}{baseAsset}挂单成功')
            continue
        order = place_order('Bid', buy_price, buy_qty)
        if order:
            print(f'在{buy_price}买入/做多{buy_qty}{baseAsset}挂单成功')
            grid_orders.append(order['id'])
            if marketType == 'SPOT':
                quote_balance -= (buy_price * buy_qty)
            else:
                free_equity -= (buy_price * buy_qty * leverage_factor)

    # 卖单：往上挂 priceStep 整数倍的价格
    for i in range(numOrders):
        sell_price = format_decimal((last_trade_price + (i + 1) * priceStep), unitPrice)
        sell_qty = format_decimal((initial_sell_qty + i * sellIncrement), unitQuantity)
        if marketType == 'SPOT':
            if base_balance < sell_qty:
                send_message(f"{baseAsset}余额: {base_balance}，无法在{sell_price}卖出{sell_qty}{baseAsset}")
                break
        else:
            if free_equity < (sell_price * sell_qty * leverage_factor):
                send_message(f"保证金余额: {free_equity}USD，无法在{sell_price}做空{sell_qty}{baseAsset}")
                break
        if dryRun:
            print(f'在{sell_price}卖出/做空{sell_qty}{baseAsset}挂单成功')
            continue
        order = place_order('Ask', sell_price, sell_qty)
        if order:
            print(f'在{sell_price}卖出/做空{sell_qty}{baseAsset}挂单成功')
            grid_orders.append(order['id'])
            if marketType == 'SPOT':
                base_balance -= sell_qty
            else:
                free_equity -= (sell_price * sell_qty * leverage_factor)

async def start_listen():
    # 取消当前挂单
    auth_api_client.cancel_open_orders(symbol=pair_name)
    # 获取最近成交记录
    last_trade = auth_api_client.get_fill_history(symbol=pair_name, marketType=marketType)
    last_trade_side = last_trade[0]['side'] if last_trade else 'Ask'
    last_trade_qty = float(last_trade[0]['quantity']) if last_trade else initialSellQuantity
    last_trade_price = (float(last_trade[0]['price']) if last_trade else 
        float(public_api_client.get_recent_trades(symbol=pair_name)[0]['price']))
    update_orders(last_trade_side, last_trade_qty, last_trade_price)
    async with websockets.connect(ws_url) as ws:
        signature = get_signature()
        sub_msg = json.dumps({"method": "SUBSCRIBE", "params": [f"account.orderUpdate.{pair_name}"], "signature": signature})
        await ws.send(sub_msg)
        while True:
            try:
                response = await ws.recv()
                data = json.loads(response)
                if data['i'] in grid_orders:
                    if data['X'] == 'Filled':
                        last_trade_side = data['S']
                        last_trade_qty = float(data['q'])
                        last_trade_price = float(data['p'])
                        update_orders(last_trade_side, last_trade_qty, last_trade_price)
                    elif data['e'] == 'orderCancelled':
                        last_trade = auth_api_client.get_fill_history(symbol=pair_name, marketType=marketType)
                        last_trade_side = last_trade[0]['side'] if last_trade else 'Ask'
                        last_trade_qty = float(last_trade[0]['quantity']) if last_trade else initialSellQuantity
                        last_trade_price = (float(last_trade[0]['price']) if last_trade else 
                            float(public_api_client.get_recent_trades(symbol=pair_name)[0]['price']))
                        update_orders(last_trade_side, last_trade_qty, last_trade_price)
                    else:
                        pass
                else:
                    continue
            except websockets.ConnectionClosed:
                send_message("连接中断，尝试重连...")
                await asyncio.sleep(3)
                break
            except Exception as e:
                send_message(f"一般错误: {e}")
                await asyncio.sleep(3)

def main():
    while True:
        try:
            loop.run_until_complete(start_listen())
        except Exception as e:
            send_message(f"一般错误: {e}")
            continue

if __name__ == "__main__":
    main()
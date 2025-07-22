import os
import time
import json
import asyncio
import traceback
import websockets
from decimal import Decimal, ROUND_HALF_UP
from dotenv import load_dotenv
from api.Public_api import PublicAPI
from api.Auth_api import AuthAPI
from api.utils import sign


use_proxy = False
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
priceStep = 0.1
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
unitPrice = Decimal(marketInfo['filters']['price']['tickSize'])
unitQuantity = Decimal(marketInfo['filters']['quantity']['stepSize'])
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
cancelled_orders = []
cancelled_orders_lock = asyncio.Lock()
trade_side_trans = {'SPOT': {'Bid': 'BUY', 'Ask': 'SELL'}, 'PERP': {'Bid': 'LONG', 'Ask': 'SHORT'}}

async def send_message(message):
    '''
    发送信息到Telegram
    '''
    print(message)  # 输出到日志
    # if not dryRun:
    #     await bot.send_message(chat_id=chat_id, text=message)

def format_decimal(value, unit_value):
    """统一浮点数小数位数"""
    value = Decimal(str(value))
    unit_value = Decimal(str(unit_value))
    return str(value.quantize(unit_value, rounding=ROUND_HALF_UP))

def format_price(price):
    """价格抹零，格式化为priceStep的整数倍，并确保小数位数满足要求"""
    price = Decimal(format_decimal(price, unitPrice))
    price = (price // Decimal(str(priceStep)) * Decimal(str(priceStep)))
    return str(price)

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

async def place_order(side, price, quantity):
    """挂单函数"""
    try:
        order = auth_api_client.place_order(
            symbol=pair_name,
            side=side,
            orderType='Limit',
            price=format_price(price),
            quantity=format_decimal(quantity, unitQuantity),
            timeInForce='GTC'
        )
        return order
    except Exception as e:
        await send_message(f"挂单失败!\nside: {side} price: {format_price(price)} quantity: {format_decimal(quantity, unitQuantity)}\n{traceback.format_exc()}")
        return None

async def update_orders(last_trade_side, last_trade_qty, last_trade_price):
    """检查并更新买卖挂单，保持每侧 3 个挂单"""

    global cancelled_orders

    # 取消当前挂单
    open_orders = auth_api_client.get_open_orders(symbol=pair_name, marketType=marketType)
    async with cancelled_orders_lock:
        cancelled_orders += [each['id'] for each in open_orders]
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
        buy_price = (last_trade_price - (i + 1) * priceStep)
        buy_qty = (initial_buy_qty + i * buyIncrement)
        if marketType == 'SPOT':
            if quote_balance < buy_price * buy_qty:
                warn_msg = (f'{quoteAsset}余额: {format_decimal(quote_balance, unitPrice)}，'
                    f'无法在{format_price(buy_price)}买入{format_decimal(buy_qty, unitQuantity)}{baseAsset}')
                await send_message(warn_msg)
                break
        else:
            if free_equity < (buy_price * buy_qty * leverage_factor):
                warn_msg = (f'保证金余额: {format_decimal(free_equity, unitPrice)}USD，'
                    f'无法在{format_price(buy_price)}做多{format_decimal(buy_qty, unitQuantity)}{baseAsset}')
                await send_message(warn_msg)
                break
        if dryRun:
            print(f'在{format_price(buy_price)}买入/做多{format_decimal(buy_qty, unitQuantity)}{baseAsset}挂单成功')
            continue
        order = await place_order('Bid', buy_price, buy_qty)
        if order:
            print(f'在{format_price(buy_price)}买入/做多{format_decimal(buy_qty, unitQuantity)}{baseAsset}挂单成功')
            if marketType == 'SPOT':
                quote_balance -= (buy_price * buy_qty)
            else:
                free_equity -= (buy_price * buy_qty * leverage_factor)

    # 卖单：往上挂 priceStep 整数倍的价格
    for i in range(numOrders):
        sell_price = (last_trade_price + (i + 1) * priceStep)
        sell_qty = (initial_sell_qty + i * sellIncrement)
        if marketType == 'SPOT':
            if base_balance < sell_qty:
                warn_msg = (f'{baseAsset}余额: {format_decimal(base_balance, unitPrice)}，'
                    f'无法在{format_price(sell_price)}卖出{format_decimal(sell_qty, unitQuantity)}{baseAsset}')
                await send_message(warn_msg)
                break
        else:
            if free_equity < (sell_price * sell_qty * leverage_factor):
                warn_msg = (f'保证金余额: {format_decimal(free_equity, unitPrice)}USD，'
                    f'无法在{format_price(sell_price)}做空{format_decimal(sell_qty, unitQuantity)}{baseAsset}')
                await send_message(warn_msg)
                break
        if dryRun:
            print(f'在{format_price(sell_price)}卖出/做空{format_decimal(sell_qty, unitQuantity)}{baseAsset}挂单成功')
            continue
        order = await place_order('Ask', sell_price, sell_qty)
        if order:
            print(f'在{format_price(sell_price)}卖出/做空{format_decimal(sell_qty, unitQuantity)}{baseAsset}挂单成功')
            if marketType == 'SPOT':
                base_balance -= sell_qty
            else:
                free_equity -= (sell_price * sell_qty * leverage_factor)

async def start_listen():
    global cancelled_orders
    # 取消当前挂单
    auth_api_client.cancel_open_orders(symbol=pair_name)
    # 获取最近成交记录
    last_trade = auth_api_client.get_fill_history(symbol=pair_name, marketType=marketType)
    last_trade_side = last_trade[0]['side'] if last_trade else 'Ask'
    last_trade_qty = float(last_trade[0]['quantity']) if last_trade else initialSellQuantity
    last_trade_price = (float(last_trade[0]['price']) if last_trade else 
        float(public_api_client.get_recent_trades(symbol=pair_name)[0]['price']))
    async with websockets.connect(ws_url) as ws:
        signature = get_signature()
        sub_msg = json.dumps({"method": "SUBSCRIBE", "params": [f"account.orderUpdate.{pair_name}"], "signature": signature})
        await ws.send(sub_msg)
        asyncio.create_task(update_orders(last_trade_side, last_trade_qty, last_trade_price))
        while True:
            try:
                response = await ws.recv()
                data = json.loads(response)['data']
                if data['X'] == 'Filled':
                    last_trade_side = data['S']
                    last_trade_qty = float(data['q'])
                    last_trade_price = float(data['p'])
                    send_message(f"{trade_side_trans[marketType][last_trade_side]} {last_trade_qty}{baseAsset} at {last_trade_price}")
                    asyncio.create_task(update_orders(last_trade_side, last_trade_qty, last_trade_price))
                elif data['e'] == 'orderCancelled':
                    if data['i'] in cancelled_orders:
                        async with cancelled_orders_lock:
                            cancelled_orders.remove(data['i'])
                        continue
                    else:
                        last_trade = auth_api_client.get_fill_history(symbol=pair_name, marketType=marketType)
                        last_trade_side = last_trade[0]['side'] if last_trade else 'Ask'
                        last_trade_qty = float(last_trade[0]['quantity']) if last_trade else initialSellQuantity
                        last_trade_price = (float(last_trade[0]['price']) if last_trade else 
                            float(public_api_client.get_recent_trades(symbol=pair_name)[0]['price']))
                        asyncio.create_task(update_orders(last_trade_side, last_trade_qty, last_trade_price))
                else:
                    continue
            except websockets.ConnectionClosed:
                await send_message("连接中断，尝试重连...")
                await asyncio.sleep(3)
                break
            except Exception as e:
                await send_message(f"一般错误: \n{str(e)}\n{traceback.format_exc()}")
                await asyncio.sleep(3)

def main():
    while True:
        try:
            loop.run_until_complete(start_listen())
        except Exception as e:
            loop.run_unitl_complete(send_message(f"一般错误: {e}"))
            continue

if __name__ == "__main__":
    main()
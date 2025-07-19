import os
import math
import time
import traceback
from dotenv import load_dotenv
from api.Public_api import PublicAPI
from api.Auth_api import AuthAPI


use_proxy = True
if use_proxy == True:
    proxy = 'http://127.0.0.1:7890'
else:
    proxy = None

public_api_client = PublicAPI(proxy=proxy)

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

# 初始化Backpack API客户端
load_dotenv()
api_key = os.getenv('API_KEY')
api_secret = os.getenv('API_SECRET')
auth_api_client = AuthAPI(api_key=api_key, api_secret=api_secret, proxy=proxy)

# 初始化Telegram Bot
# bot_token = os.getenv('BOT_TOKEN')
# chat_id = os.getenv('CHAT_ID')
# bot = telegram.Bot(bot_token)
# loop = asyncio.new_event_loop()
# asyncio.set_event_loop(loop)

# 辅助变量
buy_orders = []
sell_orders = []
last_refer_price = 0
trade_side_trans = {'Bid': 'BUY', 'Ask': 'SELL'}

def send_message(message):
    '''
    发送信息到Telegram
    '''
    print(message)  # 输出到日志
    # if not dryRun:
    #     loop.run_until_complete(bot.send_message(chat_id=chat_id, text=message))

def format_price(price):
    """价格抹零，格式化为priceStep的整数倍"""
    return float(price) // priceStep * priceStep

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

def wait_asset_unlock(base_balance, quote_balance, attempts=10, wait_time=1):
    """检查是否所有挂单已取消，资金解锁"""
    for attempt in range(attempts):
        balance = get_balance()
        base_free_balance = balance[baseAsset]['free']
        quote_free_balance = balance[quoteAsset]['free']
        if (math.isclose(base_free_balance, base_balance, abs_tol=1e-9) and 
            math.isclose(quote_free_balance, quote_balance, abs_tol=1e-9)):
            return True
        else:
            if attempt < attempts - 1:
                print(f"资金尚未全部解锁，等待{wait_time}秒再检查... (尝试 {attempt + 1}/{attempts})")
                time.sleep(wait_time)
    # 仍未解锁
    print("资金未能全部解锁，退出程序。")
    return False

def place_order(side, price, quantity):
    """挂单函数"""
    try:
        order = auth_api_client.place_order(
            symbol=pair_name,
            side=side,
            orderType='Limit',
            price=(price // unitPrice * unitPrice),
            quantity=(quantity // unitQuantity * unitQuantity),
            timeInForce='GTC'
        )
        return order
    except Exception as e:
        send_message(f"挂单失败!\n{str(e)}")
        return None

def update_orders(current_price):
    """检查并更新买卖挂单，保持每侧 3 个挂单"""
    global buy_orders, sell_orders, last_refer_price

    # 获取余额
    if marketType == 'SPOT':
        balance = get_balance()
        base_balance = (balance[baseAsset]['free'] + balance[baseAsset]['locked']) if baseAsset in balance.keys() else 0
        quote_balance = balance[quoteAsset]['free'] + balance[quoteAsset]['locked'] if quoteAsset in balance.keys() else 0
    else:
        collaterals = auth_api_client.get_collaterals()
        free_equity = float(collaterals['netEquityAvailable'])
        leverage_factor = float(collaterals['imf'])

    # 检查是否有挂单成交
    open_orders = auth_api_client.get_open_orders(symbol=pair_name, marketType=marketType)
    open_orders = [order['id'] for order in open_orders]
    filled_orders = set(buy_orders + sell_orders) - set(open_orders)

    # 获取最后一笔成交信息作为初始数据
    last_trade = auth_api_client.get_fill_history(symbol=pair_name, marketType=marketType)[0]
    last_trade_side = last_trade['side']
    last_trade_qty = float(last_trade['quantity'])
    last_trade_price = float(last_trade['price'])

    # 挂单没有减少，分情况处理
    if not filled_orders:
        # 卖单一侧有挂单
        if sell_orders:
            print('等待挂单成交...')
            return
        # 只有买单一侧有挂单(仓位已清空，追高接货)
        elif buy_orders:
            if current_price >= (last_refer_price + priceStep):
                # 风控
                if current_price < (last_trade_price + 10 * priceStep):
                    refer_price = (last_refer_price + priceStep)
                else:
                    print('价格偏离最近成交价太远，停止挂买单')
                    return
            else:
                print('等待挂单成交...')
                return
        # 买卖两侧均无挂单(首次启动)
        else:
            refer_price = format_price(last_trade_price)
    # 挂单减少(成交或取消)
    else:
        # 由于耗时较长，先取消剩余挂单
        auth_api_client.cancel_open_orders(symbol=pair_name)
        # 由于数据库订单状态更新缓慢，不确认消失的订单是成交还是取消，一律当作成交
        refer_price = last_refer_price
        filled_message = ''
        for order in filled_orders:
            filled_order_info = auth_api_client.get_orders(orderId=order)
            while not filled_order_info:
                print('aaa')
                time.sleep(1)
                filled_order_info = auth_api_client.get_orders(orderId=order)
            order_info = filled_order_info[0]
            # if order_info['status'] == 'Filled':  # 不检查，全部视为成交
            filled_trade_side = order_info['side']
            filled_trade_qty = float(order_info['quantity'])
            filled_trade_price = float(order_info['price'])
            filled_message += f"{trade_side_trans[filled_trade_side]} {filled_trade_qty}{baseAsset} at {filled_trade_price}"
            if filled_trade_side == 'Bid':
                refer_price -= priceStep
            else:
                refer_price += priceStep
            last_trade_side = filled_trade_side
            last_trade_qty = filled_trade_qty

    # # 资金是否全部解锁
    # if not wait_asset_unlock(base_balance, quote_balance):
    #     send_message("资金尚未全部解锁，无法创建新挂单")
    #     return

    # 取消剩余挂单
    auth_api_client.cancel_open_orders(symbol=pair_name)

    # 发送成交信息
    if filled_orders and filled_message:
        send_message(filled_message)

    buy_orders.clear()
    sell_orders.clear()

    if last_trade_side == 'Bid':
        initial_buy_qty = last_trade_qty + buyIncrement
        initial_sell_qty = initialSellQuantity
    else:
        initial_buy_qty = initialBuyQuantity
        initial_sell_qty = last_trade_qty + sellIncrement

    # 买单：往下挂 priceStep 整数倍的价格
    for i in range(numOrders):
        buy_price = ((refer_price - (i + 1) * priceStep) // unitPrice * unitPrice)
        buy_qty = ((initial_buy_qty + i * buyIncrement) // unitQuantity * unitQuantity)
        if marketType == 'SPOT':
            if quote_balance < buy_price * buy_qty:
                send_message(f"{quoteAsset}余额: {quote_balance}，无法在{buy_price}买入{buy_qty}{baseAsset}")
                break
        else:
            if free_equity < (buy_price * buy_qty * leverage_factor):
                send_message(f"保证金余额: {free_equity}USD，无法在{buy_price}买入多单{buy_qty}{baseAsset}")
                break
        if dryRun:
            print(f'在{buy_price}买入{buy_qty}{baseAsset}挂单成功')
            continue
        order = place_order('Bid', buy_price, buy_qty)
        if order:
            print(f'在{buy_price}买入{buy_qty}{baseAsset}挂单成功')
            buy_orders.append(order['id'])
            if marketType == 'SPOT':
                quote_balance -= (buy_price * buy_qty)
            else:
                free_equity -= (buy_price * buy_qty * leverage_factor)

    # 卖单：往上挂 priceStep 整数倍的价格
    for i in range(numOrders):
        sell_price = ((refer_price + (i + 1) * priceStep) // unitPrice * unitPrice)
        sell_qty = ((initial_sell_qty + i * sellIncrement) // unitQuantity * unitQuantity)
        if marketType == 'SPOT':
            if base_balance < sell_qty:
                print(f"{baseAsset}余额: {base_balance}，无法在{sell_price}卖出{sell_qty}{baseAsset}")
                break
        else:
            if free_equity < (sell_price * sell_qty * leverage_factor):
                send_message(f"保证金余额: {free_equity}USD，无法在{sell_price}买入空单{sell_qty}{baseAsset}")
                break
        if dryRun:
            print(f'在{sell_price}卖出{sell_qty}{baseAsset}挂单成功')
            continue
        order = place_order('Ask', sell_price, sell_qty)
        if order:
            print(f'在{sell_price}卖出{sell_qty}{baseAsset}挂单成功')
            sell_orders.append(order['id'])
            if marketType == 'SPOT':
                base_balance -= sell_qty
            else:
                free_equity -= (sell_price * sell_qty * leverage_factor)

    # 记录参考价
    last_refer_price = (refer_price // unitPrice * unitPrice)

def main():
    """主程序：实时更新价格，执行网格交易"""
    # send_message('程序启动')
    while True:
        try:
            # 获取最新价格
            current_price = float(public_api_client.get_recent_trades(symbol=pair_name)[0]['price'])
            print(f"最新价格: {current_price}")

            # 更新挂单
            update_orders(current_price)

            # 间隔 3 秒更新价格
            time.sleep(3)

        except Exception as e:
            traceback.print_exc()
            send_message(f"一般错误: {str(e)}")
            time.sleep(60)  # 发生其他错误后短暂暂停再重试

if __name__ == "__main__":
    main()
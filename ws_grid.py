import os
import time
import json
import asyncio
import telegram
import traceback
import threading
import websockets
import concurrent.futures
from decimal import Decimal, ROUND_HALF_UP
from dotenv import load_dotenv
from api.Public_api import PublicAPI
from api.Auth_api import AuthAPI
from api.utils import sign


# 初始化Backpack API客户端
load_dotenv()
api_key = os.getenv('API_KEY')
api_secret = os.getenv('API_SECRET')
public_api_client = PublicAPI()
auth_api_client = AuthAPI(api_key=api_key, api_secret=api_secret)
ws_url = 'wss://ws.backpack.exchange'

# 配置参数
initialBuyQuantity=0.2
buyIncrement=0.01
initialSellQuantity=0.2
sellIncrement=0.0
priceStep = 5.0
baseAsset = 'TAO'
quoteAsset = 'USDC'
numOrders = 3
dryRun = False
marketType = 'PERP'
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
bot_token = os.getenv('BOT_TOKEN')
chat_id = os.getenv('CHAT_ID')
bot = telegram.Bot(bot_token)
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

# 全局变量
task_queue = asyncio.Queue()
executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
cancelled_orders = []  # 记录程序本身取消的订单号，防止触发订单取消事件进入死循环
cancelled_orders_lock = threading.Lock()
filled_orders = []  # 记录成交的订单号，防止websocket重复发送消息导致重复挂单
trade_side_trans = {'SPOT': {'Bid': 'BUY', 'Ask': 'SELL'}, 'PERP': {'Bid': 'LONG', 'Ask': 'SHORT'}}

# 添加任务消费者重启标志
task_consumer_running = False
task_consumer_lock = asyncio.Lock()

async def task_consumer():
    """任务消费者，按顺序执行队列中的任务"""
    global task_consumer_running
    
    async with task_consumer_lock:
        task_consumer_running = True
    
    while True:
        try:
            func, args, kwargs = await task_queue.get()
            
            # 在线程池中执行同步函数，添加异常处理
            try:
                await loop.run_in_executor(executor, func, *args, **kwargs)
            except Exception as e:
                # 记录任务执行错误，但不让消费者崩溃
                error_msg = f"任务执行失败: {func.__name__} - {str(e)}"
                send_message(error_msg)
                print(f"Task execution error: {traceback.format_exc()}")
            
            task_queue.task_done()
            
        except asyncio.CancelledError:
            # 任务被取消，正常退出
            break
        except Exception as e:
            # 其他未预期的错误
            error_msg = f"任务消费者错误: {str(e)}"
            send_message(error_msg)
            print(f"Task consumer error: {traceback.format_exc()}")
            # 继续运行，不让消费者崩溃
            continue
    
    async with task_consumer_lock:
        task_consumer_running = False

async def ensure_task_consumer():
    """确保任务消费者正在运行"""
    async with task_consumer_lock:
        if not task_consumer_running:
            send_message("重启任务消费者...")
            loop.create_task(task_consumer())

def add_task(func, *args, **kwargs):
    """添加任务到队列（非阻塞）"""
    task_queue.put_nowait((func, args, kwargs))

def send_message(message):
    """发送信息到Telegram"""
    print(message)  # 输出到日志
    if not dryRun:
        try:
            asyncio.run_coroutine_threadsafe(bot.send_message(chat_id=chat_id, text=message), loop)
        except Exception as e:
            print(f"发送Telegram消息失败: {e}")

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

def format_qty(quantity):
    """交易数量格式化，确保交易数量符合API要求"""
    quantity = Decimal(format_decimal(quantity, unitQuantity))
    quantity = (quantity // Decimal(str(unitQuantity)) * Decimal(str(unitQuantity)))
    return str(quantity)

def get_balance():
    """获取资产余额，添加超时和重试机制"""
    balance = {baseAsset: {'free': 0.0, 'locked': 0.0}, quoteAsset: {'free': 0.0, 'locked': 0.0}}
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            raw_collaterals = auth_api_client.get_collaterals()['collateral']
            collaterals = {}
            for each in raw_collaterals:
                symbol = each['symbol']
                collaterals[symbol] = float(each['lendQuantity'])
            
            balances = auth_api_client.get_balances()
            for each in [baseAsset, quoteAsset]:
                if each in balances.keys():
                    balance[each]['free'] = float(balances[each]['available'])
                    balance[each]['locked'] = float(balances[each]['locked'])
                if each in collaterals.keys():
                    balance[each]['free'] += collaterals[each]
            return balance
            
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"获取余额失败，重试 ({attempt + 1}/{max_retries}): {e}")
                time.sleep(2 ** attempt)  # 指数退避
            else:
                raise e

def get_signature():
    """生成Websocket连接所需签名"""
    ts_ms = str(int((time.time())*1000))
    str_to_sign = f'instruction=subscribe&timestamp={ts_ms}&window=5000'
    signature = sign(str_to_sign, api_secret)
    signature_list = [api_key, signature, ts_ms, "5000"]
    return signature_list

def place_order(side, price, quantity):
    """挂单函数，添加重试机制"""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            order = auth_api_client.place_order(
                symbol=pair_name,
                side=side,
                orderType='Limit',
                price=format_price(price),
                quantity=format_qty(quantity),
                timeInForce='GTC'
            )
            return order
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"挂单失败，重试 ({attempt + 1}/{max_retries}): {e}")
                time.sleep(2 ** attempt)
            else:
                send_message(f"挂单失败!\nside: {side} price: {price} quantity: {quantity}\n{str(e)}")
                return None

def safe_api_call(func, *args, **kwargs):
    """安全的API调用，带重试和超时处理"""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                print(f"API调用失败，{wait_time}秒后重试 ({attempt + 1}/{max_retries}): {str(e)}")
                time.sleep(wait_time)
            else:
                raise e

def update_orders(last_trade_side, last_trade_qty, last_trade_price):
    """检查并更新买卖挂单，保持每侧 3 个挂单"""

    global cancelled_orders

    try:
        # 取消当前挂单 - 使用安全的API调用
        open_orders = safe_api_call(auth_api_client.get_open_orders, symbol=pair_name, marketType=marketType)
        
        with cancelled_orders_lock:
            cancelled_orders += [each['id'] for each in open_orders]
        
        while open_orders:
            safe_api_call(auth_api_client.cancel_open_orders, symbol=pair_name)
            time.sleep(1)
            open_orders = safe_api_call(auth_api_client.get_open_orders, symbol=pair_name, marketType=marketType)

        # 获取余额
        if marketType == 'SPOT':
            balance = get_balance()
            base_balance = (balance[baseAsset]['free'] + balance[baseAsset]['locked']) if baseAsset in balance.keys() else 0
            quote_balance = balance[quoteAsset]['free'] + balance[quoteAsset]['locked'] if quoteAsset in balance.keys() else 0
        else:
            collaterals = safe_api_call(auth_api_client.get_collaterals)
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
                        f'无法在{format_price(buy_price)}买入{format_qty(buy_qty)}{baseAsset}')
                    send_message(warn_msg)
                    break
            else:
                if free_equity < (buy_price * buy_qty * leverage_factor):
                    warn_msg = (f'保证金余额: {format_decimal(free_equity, unitPrice)}USD，'
                        f'无法在{format_price(buy_price)}做多{format_qty(buy_qty)}{baseAsset}')
                    send_message(warn_msg)
                    break
            if dryRun:
                print(f'在{format_price(buy_price)}买入/做多{format_qty(buy_qty)}{baseAsset}挂单成功')
                continue
            order = place_order('Bid', buy_price, buy_qty)
            if order:
                print(f'在{format_price(buy_price)}买入/做多{format_qty(buy_qty)}{baseAsset}挂单成功')
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
                        f'无法在{format_price(sell_price)}卖出{format_qty(sell_qty)}{baseAsset}')
                    send_message(warn_msg)
                    break
            else:
                if free_equity < (sell_price * sell_qty * leverage_factor):
                    warn_msg = (f'保证金余额: {format_decimal(free_equity, unitPrice)}USD，'
                        f'无法在{format_price(sell_price)}做空{format_qty(sell_qty)}{baseAsset}')
                    send_message(warn_msg)
                    break
            if dryRun:
                print(f'在{format_price(sell_price)}卖出/做空{format_qty(sell_qty)}{baseAsset}挂单成功')
                continue
            order = place_order('Ask', sell_price, sell_qty)
            if order:
                print(f'在{format_price(sell_price)}卖出/做空{format_qty(sell_qty)}{baseAsset}挂单成功')
                if marketType == 'SPOT':
                    base_balance -= sell_qty
                else:
                    free_equity -= (sell_price * sell_qty * leverage_factor)
                    
    except Exception as e:
        error_msg = f"更新订单失败: {str(e)}"
        send_message(error_msg)
        print(f"Update orders error: {traceback.format_exc()}")
        # 不重新抛出异常，避免任务消费者崩溃

async def start_listen():
    global cancelled_orders, filled_orders
    
    try:
        # 取消当前挂单
        safe_api_call(auth_api_client.cancel_open_orders, symbol=pair_name)
        
        # 获取最近成交记录
        last_trade = safe_api_call(auth_api_client.get_fill_history, symbol=pair_name, marketType=marketType)
        last_trade_side = last_trade[0]['side'] if last_trade else 'Ask'
        last_trade_qty = float(last_trade[0]['quantity']) if last_trade else initialSellQuantity
        last_trade_price = (float(last_trade[0]['price']) if last_trade else 
            float(safe_api_call(public_api_client.get_recent_trades, symbol=pair_name)[0]['price']))
            
    except Exception as e:
        send_message(f"初始化失败: {str(e)}")
        raise
    
    async with websockets.connect(ws_url) as ws:
        signature = get_signature()
        sub_msg = json.dumps({"method": "SUBSCRIBE", "params": [f"account.orderUpdate.{pair_name}"], "signature": signature})
        await ws.send(sub_msg)
        
        # 确保任务消费者正在运行
        await ensure_task_consumer()
        add_task(update_orders, last_trade_side, last_trade_qty, last_trade_price)
        
        while True:
            try:
                response = await ws.recv()
                data = json.loads(response)['data']
                
                # 定期检查任务消费者状态
                await ensure_task_consumer()
                
                if data['X'] == 'Filled':
                    # 新的成交订单
                    if data['i'] not in filled_orders:
                        last_trade_side = data['S']
                        last_trade_qty = float(data['q'])
                        last_trade_price = float(data['p'])
                        fill_msg = f"{trade_side_trans[marketType][last_trade_side]} {last_trade_qty}{baseAsset} at {last_trade_price}"
                        add_task(send_message, fill_msg)
                        add_task(update_orders, last_trade_side, last_trade_qty, last_trade_price)
                        filled_orders.append(data['i'])
                    # 已处理的成交订单(websocket服务器重复发送)
                    else:
                        continue
                elif data['e'] == 'orderCancelled':
                    with cancelled_orders_lock:
                        # 程序本身更新订单时取消的订单，不处理
                        if data['i'] in cancelled_orders:
                            continue
                        # 人为取消的订单，重新挂单补上
                        else:
                            try:
                                last_trade = safe_api_call(auth_api_client.get_fill_history, symbol=pair_name, marketType=marketType)
                                last_trade_side = last_trade[0]['side'] if last_trade else 'Ask'
                                last_trade_qty = float(last_trade[0]['quantity']) if last_trade else initialSellQuantity
                                last_trade_price = (float(last_trade[0]['price']) if last_trade else 
                                    float(safe_api_call(public_api_client.get_recent_trades, symbol=pair_name)[0]['price']))
                                add_task(update_orders, last_trade_side, last_trade_qty, last_trade_price)
                            except Exception as e:
                                send_message(f"处理订单取消事件失败: {str(e)}")
                else:
                    continue
                    
            except websockets.ConnectionClosed:
                send_message("连接中断，尝试重连...")
                # 抛出异常，让外层主函数统一处理等待和重试
                raise
            except Exception as e:
                send_message(f"WebSocket消息处理错误: {str(e)}")
                print(f"WebSocket message processing error: {traceback.format_exc()}")
                # 继续监听，不因单个消息错误而中断

def main():
    retry_count = 0
    # 启动任务消费者
    loop.create_task(task_consumer())
    
    while True:
        try:
            loop.run_until_complete(start_listen())
            retry_count = 0
        except KeyboardInterrupt:
            send_message("程序被用户中断")
            break
        except Exception as e:
            retry_count += 1
            delay = min(2 ** retry_count, 600)  # 指数增长，最大600秒
            send_message(f"程序错误，{delay}秒后重试 (第{retry_count}次): {str(e)}")
            print(f"Main loop error: {traceback.format_exc()}")
            time.sleep(delay)
            continue

if __name__ == "__main__":
    main()
import os
from dotenv import load_dotenv
from api.Public_api import PublicAPI
from api.Auth_api import AuthAPI


use_proxy = True
if use_proxy == True:
    proxy = 'http://127.0.0.1:7890'
else:
    proxy = None

load_dotenv()
api_key = os.getenv('API_KEY')
api_secret = os.getenv('API_SECRET')

# Public Endpoints
public_api_client = PublicAPI(proxy=proxy)

# Get all supported assets
result = public_api_client.get_assets()

# Get collateral parameters for assets
# result = public_api_client.get_collateral()

# Get borrow lend markets
# result = public_api_client.get_borrow_lend_markets()

# Get borrow lend market history
# result = public_api_client.get_borrow_lend_markets_history('1d', 'SOL')

# Retrieves all the markets that are supported by the exchange
# result = public_api_client.get_markets()

# Retrieves a market supported by the exchange
# result = public_api_client.get_market('SOL_USDC')

# Retrieves summarised statistics for the given market symbol
# result = public_api_client.get_ticker('SOL_USDC', '1d')

# Retrieves summarised statistics for all market symbols
# result = public_api_client.get_tickers('1d')

# Retrieves the order book depth for a given market symbol
# result = public_api_client.get_depth('SOL_USDC')

# Get K-Lines for the given market symbol
# result = public_api_client.get_k_lines('SOL_USDC', '1h', '1750694400', '1750795200', 'Last')

# Retrieves mark price, index price and the funding rate
# result = public_api_client.get_mark_prices('SOL_USDC_PERP')

# Retrieves the current open interest for the given market
# result = public_api_client.get_open_interest('SOL_USDC_PERP')

# Funding interval rate history for futures
# result = public_api_client.get_funding_rate('SOL_USDC_PERP', 100, 0)

# Get the system status, and the status message, if any
# result = public_api_client.get_status()

# Responds with pong
# result = public_api_client.ping_test()

# Retrieves the current system time
# result = public_api_client.get_system_time()

# Retrieve the most recent trades for a symbol
# result = public_api_client.get_recent_trades('SOL_USDC', 1000)

# Retrieves all historical trades for the given symbol
# result = public_api_client.get_historical_trades('SOL_USDC', 1000, 1000)

print(result)

# Authenticated Endpoints
auth_api_client = AuthAPI(api_key=api_key, api_secret=api_secret, proxy=proxy)

# Get account
result = auth_api_client.get_account()

# Update account
# result = auth_api_client.update_account(True, False, False, '2')

# Convert a dust balance on an account
# result = auth_api_client.convert_dust('SOL')

# Retrieves the maxmimum quantity an account can borrow for a given asset
# result = auth_api_client.get_max_borrow_quant('SOL')

# Retrieves the maxmimum quantity an account can trade for a given symbol
# result = auth_api_client.get_max_order_quant('SOL_USDC', 'Bid', '150', True, True, True, True)

# Retrieves the maxmimum quantity an account can withdraw for a given asset
# result = auth_api_client.get_max_withdraw_quant('SOL', True, True)

# Retrieves all the open borrow lending positions for the account
# result = auth_api_client.get_borrow_lend_position()

# Execute borrow lend
# result = auth_api_client.make_borrow_lend_order('10', 'Borrow', 'USDC')

# Retrieves account balances and the state of the balances (locked or available)
# result = auth_api_client.get_balances()

# Retrieves collateral information for an account
# result = auth_api_client.get_collaterals()

# Retrieves deposit history
# result = auth_api_client.get_deposits()

# Retrieves the user specific deposit address if the user were to deposit on the specified blockchain
# result = auth_api_client.get_deposit_address('Solana')

# Retrieves withdrawal history
# result = auth_api_client.get_withdrawals()

# Requests a withdrawal from the exchange
# result = auth_api_client.request_withdraw('2U6Fktw9x6P2BYZ7YhXtQxp3EZjK1KcbRs152CaEkMzv', 'Solana', '0.1', 'SOL')

# Retrieves account position summary
# result = auth_api_client.get_open_futures_positions()

# History of borrow and lend operations for the account
# result = auth_api_client.get_borrow_lend_history()

# History of the interest payments for borrows and lends for the account
# result = auth_api_client.get_interest_history()

# History of borrow and lend positions for the account
# result = auth_api_client.get_borrow_lend_position_history()

# Retrieves the dust conversion history for the user
# result = auth_api_client.get_dust_convert_history()

# Retrieves historical fills, with optional filtering for a specific order or symbol
# result = auth_api_client.get_fill_history()

# Users funding payment history for futures
# result = auth_api_client.get_fundings()

# Retrieves the order history for the user
# result = auth_api_client.get_orders()

# History of profit and loss realization for an account
# result = auth_api_client.get_pnls()

# Retrieves the rfq history for the user
# result = auth_api_client.get_rfqs()

# Retrieves the quote history for the user
# result = auth_api_client.get_quotes()

# History of settlement operations for the account
# result = auth_api_client.get_settlements()

# Retrieves the strategy history for the user
# result = auth_api_client.get_strategies()

# Retrieves an open order from the order book
# result = auth_api_client.get_open_order('SOL_USDC', orderId='3026090657')

# Submits an order to the matching engine for execution
# result = auth_api_client.place_order('SOL_USDC', 'Bid', 'Limit', price=156.78, quantity=0.05, postOnly=True, timeInForce='GTC')

# Cancels an open order from the order book
# result = auth_api_client.cancel_open_order('SOL_USDC', orderId='3026090657')

# Submits a set of orders to the matching engine for execution in a batch
# result = auth_api_client.place_batch_orders([
#     {'symbol': 'SOL_USDC', 'side': 'Bid', 'orderType': 'Limit', 'price': 156.78, 'quantity': 0.03, 'postOnly': True, 'timeInForce': 'GTC'},
#     {'symbol': 'SOL_USDC', 'side': 'Bid', 'orderType': 'Limit', 'price': 154.32, 'quantity': 0.03, 'postOnly': True, 'timeInForce': 'GTC'}])

# Retrieves all open orders
# result = auth_api_client.get_open_orders()

# Cancels all open orders on the specified market
# result = auth_api_client.cancel_open_orders('SOL_USDC')

# Submit a Request for Quote (RFQ)
# result = auth_api_client.submit_rfq()

# Accept a specific quote from a maker in response to an RFQ
# result = auth_api_client.accept_quote()

# Refresh a RFQ, extending the time window it is available for
# result = auth_api_client.refresh_rfq()

# Cancel a RFQ
# result = auth_api_client.cancel_rfq()

# Submit a quote in response to an RFQ
# result = auth_api_client.submit_quote()

print(result)
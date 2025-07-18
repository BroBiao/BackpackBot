from collections import namedtuple


API_URL = 'https://api.backpack.exchange'

CONTENT_TYPE = 'Content-Type'
X_API_KEY = 'X-API-KEY'
X_SIGNATURE = 'X-SIGNATURE'
X_TIMESTAMP = 'X-TIMESTAMP'
X_WINDOW = 'X-WINDOW'
DEFAULT_WINDOW = '5000'

APPLICATION_JSON = 'application/json'

# Endpoint Type
PUBLIC = 'public'
AUTH = 'Authenticated'

# Request Method
GET = "GET"
POST = "POST"
PATCH = "PATCH"
DEL = "DELETE"


Endpoint = namedtuple('Endpoint',['type', 'method', 'path', 'instruction'])

# Public Endpoints
# Assets
ASSETS = Endpoint(PUBLIC, GET, '/api/v1/assets', None)  # Get assets
COLLATERAL = Endpoint(PUBLIC, GET, '/api/v1/collateral', None) # Get collateral
# Borrow Lend Markets
BORROW_LEND_MARKETS = Endpoint(PUBLIC, GET, '/api/v1/borrowLend/markets', None)  # Get borrow lend markets
BORROW_LEND_MARKETS_HISTORY = Endpoint(PUBLIC, GET, '/api/v1/borrowLend/markets/history', None)  # Get borrow lend market history
# Markets
MARKETS = Endpoint(PUBLIC, GET, '/api/v1/markets', None)  # Get markets
MARKET = Endpoint(PUBLIC, GET, '/api/v1/market', None)  # Get market
TICKER = Endpoint(PUBLIC, GET, '/api/v1/ticker', None)  # Get ticker
TICKERS = Endpoint(PUBLIC, GET, '/api/v1/tickers', None)  # Get tickers
DEPTH = Endpoint(PUBLIC, GET, '/api/v1/depth', None)  # Get depth
K_LINES = Endpoint(PUBLIC, GET, '/api/v1/klines', None)  # Get K-lines
MARK_PRICES = Endpoint(PUBLIC, GET, '/api/v1/markPrices', None)  # Get all mark prices
OPEN_INTEREST = Endpoint(PUBLIC, GET, '/api/v1/openInterest', None)  # Get open interest
FUNDING_RATES = Endpoint(PUBLIC, GET, '/api/v1/fundingRates', None)  # Get funding interval rates
# System
STATUS = Endpoint(PUBLIC, GET, '/api/v1/status', None)  # Status
PING = Endpoint(PUBLIC, GET, '/api/v1/ping', None)  # Ping
SYSTEM_TIME = Endpoint(PUBLIC, GET, '/api/v1/time', None)  # Get system time
# Trades
RECENT_TRADES = Endpoint(PUBLIC, GET, '/api/v1/trades', None)  # Get recent trades
HISTORICAL_TRADES = Endpoint(PUBLIC, GET, '/api/v1/trades/history', None)  # Get historical trades

# Authenticated Endpoints
# Account
ACCOUNT = Endpoint(AUTH, GET, '/api/v1/account', 'accountQuery')  # Get account
UPDATE_ACCOUNT = Endpoint(AUTH, PATCH, '/api/v1/account', 'accountUpdate')  # Update account
CONVERT_DUST = Endpoint(AUTH, POST, '/api/v1/account/convertDust', 'convertDust')  # Convert a dust balance on an account
MAX_BORROW_QUANT = Endpoint(AUTH, GET, '/api/v1/account/limits/borrow', 'maxBorrowQuantity')  # Get max borrow quantity
MAX_ORDER_QUANT = Endpoint(AUTH, GET, '/api/v1/account/limits/order', 'maxOrderQuantity')  # Get max order quantity
MAX_WITHDRAW_QUANT = Endpoint(AUTH, GET, '/api/v1/account/limits/withdrawal', 'maxWithdrawalQuantity')  # Get max withdrawal quantity
# Borrow Lend
BORROW_LEND_POS = Endpoint(AUTH, GET, '/api/v1/borrowLend/positions', 'borrowLendPositionQuery')  # Get borrow lend positions
EXEC_BORROW_LEND = Endpoint(AUTH, POST, '/api/v1/borrowLend', 'borrowLendExecute')  # Execute borrow lend
# Capital
BALANCES = Endpoint(AUTH, GET, '/api/v1/capital', 'balanceQuery')  # Get balances
COLLATERALS = Endpoint(AUTH, GET, '/api/v1/capital/collateral', 'collateralQuery')  # Get collateral
DEPOSITS = Endpoint(AUTH, GET, '/wapi/v1/capital/deposits', 'depositQueryAll')  # Get deposits
DEPOSIT_ADDRESS = Endpoint(AUTH, GET, '/wapi/v1/capital/deposit/address', 'depositAddressQuery')  # Get deposit address
WITHDRAWALS = Endpoint(AUTH, GET, '/wapi/v1/capital/withdrawals', 'withdrawalQueryAll')  # Get withdrawals
EXEC_WITHDRAW = Endpoint(AUTH, POST, '/wapi/v1/capital/withdrawals', 'withdraw')  # Request withdrawal
# Futures
OPEN_POSITIONS = Endpoint(AUTH, GET, '/api/v1/position', 'positionQuery')  # Get open positions
# History
BORROWS = Endpoint(AUTH, GET, '/wapi/v1/history/borrowLend', 'borrowHistoryQueryAll')  # Get borrow history
INTERESTS = Endpoint(AUTH, GET, '/wapi/v1/history/interest', 'interestHistoryQueryAll')  # Get interest history
BORROW_POS_HISTORY = Endpoint(AUTH, GET, '/wapi/v1/history/borrowLend/positions', 'borrowPositionHistoryQueryAll')  # Get borrow position history
DUST_CONVERSIONS = Endpoint(AUTH, GET, '/wapi/v1/history/dust', 'dustHistoryQueryAll')  # Get dust conversion history
FILLS = Endpoint(AUTH, GET, '/wapi/v1/history/fills', 'fillHistoryQueryAll')  # Get fill history
FUNDINGS = Endpoint(AUTH, GET, '/wapi/v1/history/funding', 'fundingHistoryQueryAll')  # Get funding payments
ORDERS = Endpoint(AUTH, GET, '/wapi/v1/history/orders', 'orderHistoryQueryAll')  # Get order history
PNLS = Endpoint(AUTH, GET, '/wapi/v1/history/pnl', 'pnlHistoryQueryAll')  # Get profit and loss history
RFQS = Endpoint(AUTH, GET, '/wapi/v1/history/rfq', 'rfqHistoryQueryAll')  # Get rfq history
QUOTES = Endpoint(AUTH, GET, '/wapi/v1/history/quote', 'quoteHistoryQueryAll')  # Get quote history
SETTLEMENTS = Endpoint(AUTH, GET, '/wapi/v1/history/settlement', 'settlementHistoryQueryAll')  # Get settlement history
STRATEGIES = Endpoint(AUTH, GET, '/wapi/v1/history/strategies', 'strategyHistoryQueryAll')  # Get strategy history
# Order
OPEN_ORDER = Endpoint(AUTH, GET, '/api/v1/order', 'orderQuery')  # Get open order
EXEC_ORDER = Endpoint(AUTH, POST, '/api/v1/order', 'orderExecute')  # Execute order
CANCEL_ORDER = Endpoint(AUTH, DEL, '/api/v1/order', 'orderCancel')  # Cancel open order
EXEC_ORDERS = Endpoint(AUTH, POST, '/api/v1/orders', 'orderExecute')  # Execute orders
OPEN_ORDERS = Endpoint(AUTH, GET, '/api/v1/orders', 'orderQueryAll')  # Get open orders
CANCEL_ORDERS = Endpoint(AUTH, DEL, '/api/v1/orders', 'orderCancelAll')  # Cancel open orders
# Request For Quote
SUBMIT_RFQ = Endpoint(AUTH, POST, '/api/v1/rfq', 'rfqSubmit')  # Submit RFQ
ACCEPT_QUOTE = Endpoint(AUTH, POST, '/api/v1/rfq/accept', 'quoteAccept')  # Accept quote
REFRESH_RFQ = Endpoint(AUTH, POST, '/api/v1/rfq/refresh', 'rfqRefresh')  # Refresh RFQ
CANCEL_RFQ = Endpoint(AUTH, POST, '/api/v1/rfq/cancel', 'rfqCancel')  # Cancel RFQ
SUBMIT_QUOTE = Endpoint(AUTH, POST, '/api/v1/rfq/quote', 'quoteSubmit')  # Submit quote
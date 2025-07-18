from .client import Client
from .consts import *


class PublicAPI(Client):

    def __init__(self, proxy=None):
        Client.__init__(self, proxy=proxy)

    # Get assets
    def get_assets(self):
        return self._request_without_params(ASSETS.instruction, ASSETS.method, ASSETS.path)

    # Get collateral
    def get_collateral(self):
        return self._request_without_params(COLLATERAL.instruction, COLLATERAL.method, COLLATERAL.path)

    # Get borrow lend markets
    def get_borrow_lend_markets(self):
        return self._request_without_params(BORROW_LEND_MARKETS.instruction, BORROW_LEND_MARKETS.method, BORROW_LEND_MARKETS.path)

    # Get borrow lend market history
    def get_borrow_lend_markets_history(self, interval, symbol=None):
        params = {'interval': interval, 'symbol': symbol}
        return self._request_with_params(BORROW_LEND_MARKETS_HISTORY.instruction, BORROW_LEND_MARKETS_HISTORY.method, 
            BORROW_LEND_MARKETS_HISTORY.path, params)

    # Retrieves all the markets that are supported by the exchange
    def get_markets(self):
        return self._request_without_params(MARKETS.instruction, MARKETS.method, MARKETS.path)

    # Retrieves a market supported by the exchange
    def get_market(self, symbol):
        params = {'symbol': symbol}
        return self._request_with_params(MARKET.instruction, MARKET.method, MARKET.path, params)

    # Retrieves summarised statistics for the last 24 hours for the given market symbol
    def get_ticker(self, symbol, interval=None):
        params = {'symbol': symbol, 'interval': interval}
        return self._request_with_params(TICKER.instruction, TICKER.method, TICKER.path, params)

    # Retrieves summarised statistics for the last 24 hours for all market symbols
    def get_tickers(self, interval=None):
        params = {'interval': interval}
        return self._request_with_params(TICKERS.instruction, TICKERS.method, TICKERS.path, params)

    # Retrieves the order book depth for a given market symbol
    def get_depth(self, symbol):
        params = {'symbol': symbol}
        return self._request_with_params(DEPTH.instruction, DEPTH.method, DEPTH.path, params)

    # Get K-Lines for the given market symbol
    def get_k_lines(self, symbol, interval, startTime, endTime=None, priceType=None):
        params = {'symbol': symbol, 'interval': interval, 'startTime': startTime,
                  'endTime': endTime, 'priceType': priceType}
        return self._request_with_params(K_LINES.instruction, K_LINES.method, K_LINES.path, params)

    # Retrieves mark price, index price and the funding rate
    def get_mark_prices(self, symbol=None):
        params = {'symbol': symbol}
        return self._request_with_params(MARK_PRICES.instruction, MARK_PRICES.method, MARK_PRICES.path, params)

    # Retrieves the current open interest for the given market
    def get_open_interest(self, symbol=None):
        params = {'symbol': symbol}
        return self._request_with_params(OPEN_INTEREST.instruction, OPEN_INTEREST.method, OPEN_INTEREST.path, params)

    # Funding interval rate history for futures
    def get_funding_rate(self, symbol, limit=100, offset=0):
        params = {'symbol': symbol, 'limit': limit, 'offset': offset}
        return self._request_with_params(FUNDING_RATES.instruction, FUNDING_RATES.method, FUNDING_RATES.path, params)

    # Get the system status, and the status message, if any
    def get_status(self):
        return self._request_without_params(STATUS.instruction, STATUS.method, STATUS.path)

    # Responds with pong
    def ping_test(self):
        return self._request_without_params(PING.instruction, PING.method, PING.path)

    # Retrieves the current system time
    def get_system_time(self):
        return self._request_without_params(SYSTEM_TIME.instruction, SYSTEM_TIME.method, SYSTEM_TIME.path)

    # Retrieve the most recent trades for a symbol
    def get_recent_trades(self, symbol, limit=100):
        params = {'symbol': symbol, 'limit': limit}
        return self._request_with_params(RECENT_TRADES.instruction, RECENT_TRADES.method, RECENT_TRADES.path, params)

    # Retrieves all historical trades for the given symbol
    def get_historical_trades(self, symbol, limit=100, offset=0):
        params = {'symbol': symbol, 'limit': limit, 'offset': offset}
        return self._request_with_params(HISTORICAL_TRADES.instruction, HISTORICAL_TRADES.method, HISTORICAL_TRADES.path, params)
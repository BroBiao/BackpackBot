from .client import Client
from .consts import *


class AuthAPI(Client):

    def __init__(self, api_key, api_secret, proxy=None):
        Client.__init__(self, api_key=api_key, api_secret=api_secret, proxy=proxy)

    # Get account
    def get_account(self):
        return self._request_without_params(ACCOUNT.instruction, ACCOUNT.method, ACCOUNT.path)

    # Update account
    def update_account(self, autoBorrowSettlements, autoLend, autoRepayBorrows, leverageLimit):
        params = {'autoBorrowSettlements': autoBorrowSettlements, 'autoLend': autoLend, 
                  'autoRepayBorrows': autoRepayBorrows, 'leverageLimit': leverageLimit}
        return self._request_with_params(UPDATE_ACCOUNT.instruction, UPDATE_ACCOUNT.method, UPDATE_ACCOUNT.path, params)

    # Convert a dust balance on an account
    def convert_dust(self, symbol):
        params = {'symbol': symbol}
        return self._request_with_params(CONVERT_DUST.instruction, CONVERT_DUST.method, CONVERT_DUST.path, params)

    # Retrieves the maxmimum quantity an account can borrow for a given asset
    def get_max_borrow_quant(self, symbol):
        params = {'symbol': symbol}
        return self._request_with_params(MAX_BORROW_QUANT.instruction, MAX_BORROW_QUANT.method, MAX_BORROW_QUANT.path, params)

    # Retrieves the maxmimum quantity an account can trade for a given symbol
    def get_max_order_quant(self, symbol, side, price=None, reduceOnly=True, autoBorrow=True, autoBorrowRepay=True, autoLendRedeem=True):
        params = {'symbol': symbol, 'side': side, 'price': price, 'reduceOnly': reduceOnly, 'autoBorrow': autoBorrow, 
                  'autoBorrowRepay': autoBorrowRepay, 'autoLendRedeem': autoLendRedeem}
        return self._request_with_params(MAX_ORDER_QUANT.instruction, MAX_ORDER_QUANT.method, MAX_ORDER_QUANT.path, params)

    # Retrieves the maxmimum quantity an account can withdraw for a given asset
    def get_max_withdraw_quant(self, symbol, autoBorrow=True, autoLendRedeem=True):
        params = {'symbol': symbol, 'autoBorrow': autoBorrow, 'autoLendRedeem': autoLendRedeem}
        return self._request_with_params(MAX_WITHDRAW_QUANT.instruction, MAX_WITHDRAW_QUANT.method, MAX_WITHDRAW_QUANT.path, params)

    # Retrieves all the open borrow lending positions for the account
    def get_borrow_lend_position(self):
        return self._request_without_params(BORROW_LEND_POS.instruction, BORROW_LEND_POS.method, BORROW_LEND_POS.path)

    # Execute borrow lend
    def make_borrow_lend_order(self, quantity, side, symbol):
        params = {'quantity': quantity, 'side': side, 'symbol': symbol}
        return self._request_with_params(EXEC_BORROW_LEND.instruction, EXEC_BORROW_LEND.method, EXEC_BORROW_LEND.path, params)

    # Retrieves account balances and the state of the balances (locked or available)
    def get_balances(self):
        return self._request_without_params(BALANCES.instruction, BALANCES.method, BALANCES.path)

    # Retrieves collateral information for an account
    def get_collaterals(self, subaccountId=None):
        params = {'subaccountId': subaccountId}
        return self._request_with_params(COLLATERALS.instruction, COLLATERALS.method, COLLATERALS.path, params)

    # Retrieves deposit history
    def get_deposits(self, fromTime=None, toTime=None, limit=100, offset=0):
        params = {'from': fromTime, 'to': toTime, 'limit': limit, 'offset': offset}
        return self._request_with_params(DEPOSITS.instruction, DEPOSITS.method, DEPOSITS.path, params)

    # Retrieves the user specific deposit address if the user were to deposit on the specified blockchain
    def get_deposit_address(self, blockchain):
        params = {'blockchain': blockchain}
        return self._request_with_params(DEPOSIT_ADDRESS.instruction, DEPOSIT_ADDRESS.method, DEPOSIT_ADDRESS.path, params)

    # Retrieves withdrawal history
    def get_withdrawals(self, fromTime=None, toTime=None, limit=100, offset=0):
        params = {'from': fromTime, 'to': toTime, 'limit': limit, 'offset': offset}
        return self._request_with_params(WITHDRAWALS.instruction, WITHDRAWALS.method, WITHDRAWALS.path, params)

    # Requests a withdrawal from the exchange
    def request_withdraw(self, address, blockchain, quantity, symbol, clientId=None, twoFactorToken=None, autoBorrow=True, autoLendRedeem=True):
        params = {'address': address, 'blockchain': blockchain, 'quantity': quantity, 'symbol': symbol, 'clientId': clientId,
                  'twoFactorToken': twoFactorToken, 'autoBorrow': autoBorrow, 'autoLendRedeem': autoLendRedeem}
        return self._request_with_params(EXEC_WITHDRAW.instruction, EXEC_WITHDRAW.method, EXEC_WITHDRAW.path, params)

    # Retrieves account position summary
    def get_open_futures_positions(self):
        return self._request_without_params(OPEN_POSITIONS.instruction, OPEN_POSITIONS.method, OPEN_POSITIONS.path)

    # History of borrow and lend operations for the account
    def get_borrow_lend_history(self, type=None, sources=None, positionId=None, symbol=None, limit=100, offset=0, sortDirection=None):
        params = {'type': type, 'sources': sources, 'positionId': positionId, 'symbol': symbol, 'limit': limit, 'offset': offset, 
                  'sortDirection': sortDirection}
        return self._request_with_params(BORROWS.instruction, BORROWS.method, BORROWS.path, params)

    # History of the interest payments for borrows and lends for the account
    def get_interest_history(self, asset=None, symbol=None, positionId=None, limit=100, offset=0, source=None, sortDirection=None):
        params = {'asset': asset, 'symbol': symbol, 'positionId': positionId, 'limit': limit, 'offset': offset, 'source': source, 
                  'sortDirection': sortDirection}
        return self._request_with_params(INTERESTS.instruction, INTERESTS.method, INTERESTS.path, params)

    # History of borrow and lend positions for the account
    def get_borrow_lend_position_history(self, symbol=None, side=None, state=None, limit=100, offset=0, sortDirection=None):
        params = {'symbol': symbol, 'side': side, 'state': state, 'limit': limit, 'offset': offset, 'sortDirection': sortDirection}
        return self._request_with_params(BORROW_POS_HISTORY.instruction, BORROW_POS_HISTORY.method, BORROW_POS_HISTORY.path, params)

    # Retrieves the dust conversion history for the user
    def get_dust_convert_history(self, convert_id=None, symbol=None, limit=100, offset=0, sortDirection=None):
        params = {'id': convert_id, 'symbol': symbol, 'limit': limit, 'offset': offset, 'sortDirection': sortDirection}
        return self._request_with_params(DUST_CONVERSIONS.instruction, DUST_CONVERSIONS.method, DUST_CONVERSIONS.path, params)

    # Retrieves historical fills, with optional filtering for a specific order or symbol
    def get_fill_history(self, orderId=None, strategyId=None, fromTime=None, toTime=None, symbol=None, limit=100, offset=0, 
                         fillType=None, marketType=None, sortDirection=None):
        params = {'orderId': orderId, 'strategyId': strategyId, 'from': fromTime, 'to': toTime, 'symbol': symbol, 'limit': limit, 
                  'offset': offset, 'fillType': fillType, 'marketType': marketType, 'sortDirection': sortDirection}
        return self._request_with_params(FILLS.instruction, FILLS.method, FILLS.path, params)

    # Users funding payment history for futures
    def get_fundings(self, subaccountId=None, symbol=None, limit=100, offset=0, sortDirection=None):
        params = {'subaccountId': subaccountId, 'symbol': symbol, 'limit': limit, 'offset': offset, 'sortDirection': sortDirection}
        return self._request_with_params(FUNDINGS.instruction, FUNDINGS.method, FUNDINGS.path, params)

    # Retrieves the order history for the user
    def get_orders(self, orderId=None, strategyId=None, symbol=None, limit=100, offset=0, marketType=None, sortDirection=None):
        params = {'orderId': orderId, 'strategyId': strategyId, 'symbol': symbol, 'limit': limit, 'offset': offset, 
                  'marketType': marketType, 'sortDirection': sortDirection}
        return self._request_with_params(ORDERS.instruction, ORDERS.method, ORDERS.path, params)

    # History of profit and loss realization for an account
    def get_pnls(self, subaccountId=None, symbol=None, limit=100, offset=0, sortDirection=None):
        params = {'subaccountId': subaccountId, 'symbol': symbol, 'limit': limit, 'offset': offset, 'sortDirection': sortDirection}
        return self._request_with_params(PNLS.instruction, PNLS.method, PNLS.path, params)

    # Retrieves the rfq history for the user
    def get_rfqs(self, rfqId=None, symbol=None, status=None, side=None, limit=100, offset=0, sortDirection=None):
        params = {'rfqId': rfqId, 'symbol': symbol, 'status': status, 'side': side, 'limit': limit, 'offset': offset, 
                  'sortDirection': sortDirection}
        return self._request_with_params(RFQS.instruction, RFQS.method, RFQS.path, params)

    # Retrieves the quote history for the user
    def get_quotes(self, quoteId=None, symbol=None, status=None, limit=100, offset=0, sortDirection=None):
        params = {'quoteId': quoteId, 'symbol': symbol, 'status': status, 'limit': limit, 'offset': offset, 
                  'sortDirection': sortDirection}
        return self._request_with_params(QUOTES.instruction, QUOTES.method, QUOTES.path, params)

    # History of settlement operations for the account
    def get_settlements(self, source=None, limit=100, offset=0, sortDirection=None):
        params = {'source': source, 'limit': limit, 'offset': offset, 'sortDirection': sortDirection}
        return self._request_with_params(SETTLEMENTS.instruction, SETTLEMENTS.method, SETTLEMENTS.path, params)

    # Retrieves the strategy history for the user
    def get_strategies(self, strategyId=None, symbol=None, limit=100, offset=0, marketType=None, sortDirection=None):
        params = {'strategyId': strategyId, 'symbol': symbol, 'limit': limit, 'offset': offset, 'marketType': marketType, 
                  'sortDirection': sortDirection}
        return self._request_with_params(STRATEGIES.instruction, STRATEGIES.method, STRATEGIES.path, params)

    # Retrieves an open order from the order book
    def get_open_order(self, symbol, clientId=None, orderId=None):
        params = {'symbol': symbol, 'clientId': clientId, 'orderId': orderId}
        return self._request_with_params(OPEN_ORDER.instruction, OPEN_ORDER.method, OPEN_ORDER.path, params)

    # Submits an order to the matching engine for execution
    def place_order(self, symbol, side, orderType, price=None, quantity=None, postOnly=None, timeInForce=None, quoteQuantity=None, 
                    autoLend=None, autoLendRedeem=None, autoBorrow=None, autoBorrowRepay=None, clientId=None, reduceOnly=None, 
                    selfTradePrevention=None, stopLossLimitPrice=None, stopLossTriggerBy=None, stopLossTriggerPrice=None, 
                    takeProfitLimitPrice=None, takeProfitTriggerBy=None, takeProfitTriggerPrice=None, triggerBy=None, 
                    triggerPrice=None, triggerQuantity=None):
        params = {'symbol': symbol, 'side': side, 'orderType': orderType, 'price': price, 'quantity': quantity, 
                  'postOnly': postOnly, 'quoteQuantity': quoteQuantity, 'autoLend': autoLend, 'autoLendRedeem': autoLendRedeem, 
                  'autoBorrow': autoBorrow, 'autoBorrowRepay': autoBorrowRepay, 'clientId': clientId, 'reduceOnly': reduceOnly, 
                  'selfTradePrevention': selfTradePrevention, 'stopLossLimitPrice': stopLossLimitPrice, 
                  'stopLossTriggerBy': stopLossTriggerBy, 'stopLossTriggerPrice': stopLossTriggerPrice, 
                  'takeProfitLimitPrice': takeProfitLimitPrice, 'takeProfitTriggerBy': takeProfitTriggerBy, 
                  'takeProfitTriggerPrice': takeProfitTriggerPrice, 'timeInForce': timeInForce, 'triggerBy': triggerBy, 
                  'triggerPrice': triggerPrice, 'triggerQuantity': triggerQuantity}
        return self._request_with_params(EXEC_ORDER.instruction, EXEC_ORDER.method, EXEC_ORDER.path, params)

    # Cancels an open order from the order book
    def cancel_open_order(self, symbol, orderId=None, clientId=None):
        params = {'symbol': symbol, 'orderId': orderId, 'clientId': clientId}
        return self._request_with_params(CANCEL_ORDER.instruction, CANCEL_ORDER.method, CANCEL_ORDER.path, params)

    # Submits a set of orders to the matching engine for execution in a batch
    def place_batch_orders(self, orders):
        return self._request_with_params(EXEC_ORDERS.instruction, EXEC_ORDERS.method, EXEC_ORDERS.path, orders)

    # Retrieves all open orders
    def get_open_orders(self, symbol=None, marketType=None):
        params = {'symbol': symbol, 'marketType': marketType}
        return self._request_with_params(OPEN_ORDERS.instruction, OPEN_ORDERS.method, OPEN_ORDERS.path, params)

    # Cancels all open orders on the specified market
    def cancel_open_orders(self, symbol, orderType=None):
        params = {'symbol': symbol, 'orderType': orderType}
        return self._request_with_params(CANCEL_ORDERS.instruction, CANCEL_ORDERS.method, CANCEL_ORDERS.path, params)

    # Submit a Request for Quote (RFQ)
    def submit_rfq(self, symbol, side, price=None, quantity=None, quoteQuantity=None, executionMode='AwaitAccept', clientId=None):
        params = {'symbol': symbol, 'side': side, 'price': price, 'quantity': quantity, 'quoteQuantity': quoteQuantity, 
                  'executionMode': executionMode, 'clientId': clientId}
        return self._request_with_params(SUBMIT_RFQ.instruction, SUBMIT_RFQ.method, SUBMIT_RFQ.path, params)

    # Accept a specific quote from a maker in response to an RFQ
    def accept_quote(self, quoteId, rfqId=None, clientId=None):
        params = {'quoteId': quoteId, 'rfqId': rfqId, 'clientId': clientId}
        return self._request_with_params(ACCEPT_QUOTE.instruction, ACCEPT_QUOTE.method, ACCEPT_QUOTE.path, params)

    # Refresh a RFQ, extending the time window it is available for
    def refresh_rfq(self, rfqId):
        params = {'rfqId': rfqId}
        return self._request_with_params(REFRESH_RFQ.instruction, REFRESH_RFQ.method, REFRESH_RFQ.path, params)

    # Cancel a RFQ
    def cancel_rfq(self, rfqId=None, clientId=None):
        params = {'rfqId': rfqId, 'clientId': clientId}
        return self._request_with_params(CANCEL_RFQ.instruction, CANCEL_RFQ.method, CANCEL_RFQ.path, params)

    # Submit a quote in response to an RFQ
    def submit_quote(self, rfqId, askPrice, bidPrice, clientId=None):
        params = {'rfqId': rfqId, 'askPrice': askPrice, 'bidPrice': bidPrice, 'clientId': clientId}
        return self._request_with_params(SUBMIT_QUOTE.instruction, SUBMIT_QUOTE.method, SUBMIT_QUOTE.path, params)
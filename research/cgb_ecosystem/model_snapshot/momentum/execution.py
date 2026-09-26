"""Optional price-touch accounting. These functions never fit the market model."""
import math


def _check_touch_prices(entry_bid, entry_ask, exit_bid, exit_ask):
    prices = (entry_bid, entry_ask, exit_bid, exit_ask)
    if not all(math.isfinite(x) and x > 0 for x in prices):
        raise ValueError('Prices must be finite and positive.')
    if entry_bid > entry_ask or exit_bid > exit_ask:
        raise ValueError('Crossed quotes cannot define a price-touch benchmark.')


def futures_touch_benchmark(entry_bid, entry_ask, exit_bid, exit_ask,
                            direction, contracts, cfg, fees_cad=0.0,
                            additional_slippage_ticks_per_contract=0.0):
    """Benchmark one round trip in one fixed CGB contract at supplied quotes.

    Caller must select quotes at actual entry/exit benchmark times, after latency,
    and check freshness, contract identity and sufficient depth. No fill, queue or
    market-impact model is implied. Extra slippage is TOTAL round-trip adverse
    ticks per contract beyond the displayed touches. Spread is already paid once.
    """
    _check_touch_prices(entry_bid, entry_ask, exit_bid, exit_ask)
    if direction not in (-1, 1) or contracts <= 0 or int(contracts) != contracts:
        raise ValueError('direction must be +/-1 and contracts a positive integer.')
    if not all(math.isfinite(x) and x >= 0 for x in (fees_cad, additional_slippage_ticks_per_contract)):
        raise ValueError('Fees and additional adverse slippage must be finite and nonnegative.')
    touch_points = exit_bid - entry_ask if direction == 1 else entry_bid - exit_ask
    mid_points = direction * ((exit_bid + exit_ask) / 2 - (entry_bid + entry_ask) / 2)
    multiplier = contracts * cfg.tick_value_cad / cfg.tick_size
    extra = contracts * additional_slippage_ticks_per_contract * cfg.tick_value_cad
    return {
        'midpoint_change_cad': mid_points * multiplier,
        'spread_crossing_cad': (mid_points - touch_points) * multiplier,
        'touch_change_cad': touch_points * multiplier,
        'additional_slippage_cad': extra, 'fees_cad': fees_cad,
        'net_benchmark_cad': touch_points * multiplier - extra - fees_cad,
        'status': 'price_touch_benchmark_not_verified_fills',
    }


def cash_bond_touch_benchmark(entry_bid_clean, entry_ask_clean,
                              exit_bid_clean, exit_ask_clean,
                              entry_accrued_per_100, exit_accrued_per_100,
                              face_amount, direction, position_cashflows_cad=0.0,
                              financing_and_borrow_cad=0.0, fees_cad=0.0,
                              additional_slippage_cad=0.0):
    """Simple cash-price ledger; clean prices and accrued interest are per 100 face.

    Accrued amounts must match the relevant settlement conventions. Cashflows are
    SIGNED for the actual position, including coupon receipts/payments as needed.
    Financing/borrow and additional adverse slippage are nonnegative costs here.
    This is not a bond valuation, settlement, repo, DV01 or CGB hedge-ratio engine.
    """
    _check_touch_prices(entry_bid_clean, entry_ask_clean, exit_bid_clean, exit_ask_clean)
    amounts = (entry_accrued_per_100, exit_accrued_per_100, face_amount,
               position_cashflows_cad, financing_and_borrow_cad, fees_cad, additional_slippage_cad)
    if not all(math.isfinite(x) for x in amounts) or face_amount <= 0 or direction not in (-1, 1):
        raise ValueError('Finite amounts, positive face and direction +/-1 required.')
    if min(financing_and_borrow_cad, fees_cad, additional_slippage_cad) < 0:
        raise ValueError('Cost inputs cannot be negative in this simple ledger.')
    entry = (entry_ask_clean if direction == 1 else entry_bid_clean) + entry_accrued_per_100
    exit_price = (exit_bid_clean if direction == 1 else exit_ask_clean) + exit_accrued_per_100
    price_change = direction * (exit_price - entry) * face_amount / 100
    return {'dirty_price_change_cad': price_change,
            'position_cashflows_cad': position_cashflows_cad,
            'net_benchmark_cad': price_change + position_cashflows_cad
                - financing_and_borrow_cad - fees_cad - additional_slippage_cad,
            'status': 'price_touch_ledger_not_verified_fills'}

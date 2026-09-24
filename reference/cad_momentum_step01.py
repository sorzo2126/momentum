"""Step 1 reference definitions; no trained signal and no market-data loader.

All examples/tests are synthetic. Times must be timezone-aware. Scalar as-of
selection is not an order-book reconstruction algorithm. Quote-touch P&L is a
one-level execution benchmark, not a fill guarantee.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from math import isfinite
from typing import Iterable, Sequence
import unittest

TICK = 0.01
TICK_VALUE_CAD = 10.0


def _aware(t: datetime) -> None:
    if t.tzinfo is None or t.utcoffset() is None:
        raise ValueError("A timezone-aware timestamp is required")


def _finite(*xs: float) -> None:
    if not all(isfinite(x) for x in xs):
        raise ValueError("Non-finite numerical input")


@dataclass(frozen=True)
class Observation:
    instrument: str
    quantity: str
    unit: str
    observed_at: datetime
    available_at: datetime
    value: float | None
    source: str
    valid: bool = True

    def __post_init__(self):
        _aware(self.observed_at)
        _aware(self.available_at)
        if self.available_at < self.observed_at:
            raise ValueError("Resolve clock inconsistencies before research")
        if self.value is not None:
            _finite(self.value)


@dataclass(frozen=True)
class Reading:
    value: float | None
    status: str
    age: timedelta | None
    record: Observation | None


def asof_reading(rows: Iterable[Observation], instrument: str, quantity: str,
                 source: str, unit: str, at: datetime,
                 max_age: timedelta) -> Reading:
    """Latest event known at `at`, using only revisions available then.

    An invalid newest event is not silently replaced by an older valid event.
    Conflicting duplicate event/revision timestamps require provider sequencing.
    """
    _aware(at)
    if max_age < timedelta(0):
        raise ValueError("max_age must be nonnegative")
    candidates = [r for r in rows if
                  (r.instrument, r.quantity, r.source, r.unit) ==
                  (instrument, quantity, source, unit)
                  and r.available_at <= at and r.observed_at <= at]
    if not candidates:
        return Reading(None, "missing", None, None)
    best_key = max((r.observed_at, r.available_at) for r in candidates)
    latest = [r for r in candidates
              if (r.observed_at, r.available_at) == best_key]
    if len({(r.value, r.valid) for r in latest}) != 1:
        raise ValueError("Conflicting records need a provider sequence number")
    r = latest[0]
    age = at - r.observed_at
    if not r.valid or r.value is None:
        return Reading(None, "invalid", age, r)
    if age > max_age:
        return Reading(None, "stale", age, r)
    return Reading(r.value, "valid", age, r)


def horizon_eligible(decision: datetime, latency: timedelta, horizon: timedelta,
                     session_open: datetime, flat_by: datetime) -> bool:
    for t in (decision, session_open, flat_by):
        _aware(t)
    if latency < timedelta(0) or horizon <= timedelta(0):
        raise ValueError("Invalid latency/horizon")
    if flat_by <= session_open:
        raise ValueError("Invalid operating session")
    return session_open <= decision and decision + latency + horizon <= flat_by


def common_local(cad_ticks: float, us_move: float,
                 lagged_beta_ticks_per_us_unit: float) -> tuple[float, float]:
    _finite(cad_ticks, us_move, lagged_beta_ticks_per_us_unit)
    common = lagged_beta_ticks_per_us_unit * us_move
    return common, cad_ticks - common


def curve_coordinates(dy2_bp: float, dy5_bp: float,
                      dy10_bp: float) -> tuple[float, float, float]:
    """Five-year anchor, change in 2s5s, change in 5s10s; all in bp."""
    _finite(dy2_bp, dy5_bp, dy10_bp)
    return dy5_bp, dy5_bp - dy2_bp, dy10_bp - dy5_bp


def reconstruct_curve(anchor5: float, slope25: float,
                      slope510: float) -> tuple[float, float, float]:
    _finite(anchor5, slope25, slope510)
    return anchor5 - slope25, anchor5, anchor5 + slope510


@dataclass(frozen=True)
class PathOutcome:
    endpoint_ticks: float
    mfe_ticks: float
    mae_ticks: float


def path_outcome(ordered_midpoints: Sequence[float], direction: int) -> PathOutcome:
    """Observed-path extrema, not unobserved continuous-time extrema.

    Caller must supply the complete intended horizon and a fixed contract;
    missing/censored paths must never be passed as completed labels.
    """
    if direction not in (-1, 1) or len(ordered_midpoints) < 2:
        raise ValueError("Need direction +/-1 and at least two observations")
    _finite(*ordered_midpoints)
    changes = [direction * (p - ordered_midpoints[0]) / TICK
               for p in ordered_midpoints]
    return PathOutcome(changes[-1], max(0.0, max(changes)),
                       max(0.0, -min(changes)))


@dataclass(frozen=True)
class Quote:
    contract: str
    observed_at: datetime
    available_at: datetime
    bid: float
    ask: float
    bid_size: int
    ask_size: int

    def __post_init__(self):
        _aware(self.observed_at)
        _aware(self.available_at)
        _finite(self.bid, self.ask)
        if self.available_at < self.observed_at or self.bid > self.ask:
            raise ValueError("Invalid quote timing or crossed market")
        if any(isinstance(n, bool) or not isinstance(n, int) or n < 0
               for n in (self.bid_size, self.ask_size)):
            raise ValueError("Depth must be nonnegative integer contracts")


@dataclass(frozen=True)
class ExecutionBenchmark:
    gross_ticks: float
    net_ticks: float
    net_cad: float


def quote_touch_pnl(direction: int, entry: Quote, exit: Quote,
                    entry_at: datetime, exit_at: datetime,
                    max_quote_age: timedelta, contracts: int,
                    roundtrip_fee_cad_per_contract: float,
                    extra_roundtrip_slippage_ticks: float) -> ExecutionBenchmark:
    """Cross the quoted spread once at entry and once at exit.

    Fees exclude spread/slippage. Extra slippage is beyond quoted prices.
    Depth sufficiency is a necessary condition, not a fill guarantee.
    """
    _aware(entry_at)
    _aware(exit_at)
    if direction not in (-1, 1) or isinstance(contracts, bool) or \
            not isinstance(contracts, int) or contracts < 1:
        raise ValueError("Invalid direction or quantity")
    _finite(roundtrip_fee_cad_per_contract, extra_roundtrip_slippage_ticks)
    if min(roundtrip_fee_cad_per_contract, extra_roundtrip_slippage_ticks) < 0:
        raise ValueError("Specify nonnegative explicit costs")
    if max_quote_age < timedelta(0) or exit_at <= entry_at:
        raise ValueError("Invalid quote-age limit or holding interval")
    if entry.contract != exit.contract:
        raise ValueError("Contract changed inside the outcome window")
    for q, at in ((entry, entry_at), (exit, exit_at)):
        if q.available_at > at or q.observed_at > at or \
                at - q.observed_at > max_quote_age:
            raise ValueError("Quote is unavailable or stale at execution time")
    required_sizes = ((entry.ask_size, exit.bid_size) if direction == 1
                      else (entry.bid_size, exit.ask_size))
    if min(required_sizes) < contracts:
        raise ValueError("Insufficient top-of-book size for this benchmark")
    gross = ((exit.bid - entry.ask) if direction == 1
             else (entry.bid - exit.ask)) / TICK
    net = gross - extra_roundtrip_slippage_ticks - \
        roundtrip_fee_cad_per_contract / TICK_VALUE_CAD
    return ExecutionBenchmark(gross, net, contracts * TICK_VALUE_CAD * net)


def frozen_pressure_response(pressure: float, sensitivity: float,
                             persistence: float, steps: int) -> float:
    """Illustrative expected local ticks under frozen linear coefficients.

    Assumes zero conditional means for future pressure innovations/residuals.
    This is neither parameter estimation nor a CGB physics calibration.
    """
    _finite(pressure, sensitivity, persistence)
    if isinstance(steps, bool) or not isinstance(steps, int) or steps < 1:
        raise ValueError("steps must be a positive integer")
    return sensitivity * pressure * sum(persistence ** j for j in range(steps))


class StepOneTests(unittest.TestCase):
    def setUp(self):
        self.t = datetime(2026, 9, 24, 13, 0, tzinfo=timezone.utc)

    def observation(self, value, observed=0, available=0, valid=True):
        return Observation("CAD5", "yield", "bp", self.t + timedelta(seconds=observed),
                           self.t + timedelta(seconds=available), value, "synthetic", valid)

    def read(self, rows, seconds=0, age=20):
        return asof_reading(rows, "CAD5", "yield", "synthetic", "bp",
                            self.t + timedelta(seconds=seconds), timedelta(seconds=age))

    def quote(self, seconds=0, bid=120.0, ask=120.01, contract="CGB_TEST", size=10):
        t = self.t + timedelta(seconds=seconds)
        return Quote(contract, t, t, bid, ask, size, size)

    def pnl(self, direction, entry=None, exit=None, fee=0, slip=0, size=1):
        return quote_touch_pnl(direction, entry or self.quote(),
                               exit or self.quote(60), self.t,
                               self.t + timedelta(seconds=60), timedelta(seconds=1),
                               size, fee, slip)

    def test_future_revision_cannot_rewrite_past(self):
        rows = [self.observation(300), self.observation(310, available=10)]
        self.assertEqual(self.read(rows).value, 300)
        self.assertEqual(self.read(rows, 10).value, 310)

    def test_late_old_event_does_not_replace_new_event(self):
        rows = [self.observation(300), self.observation(301, 5, 5),
                self.observation(999, 0, 10)]
        self.assertEqual(self.read(rows, 10).value, 301)

    def test_missing_stale_invalid_and_zero_are_distinct(self):
        self.assertEqual(self.read([]).status, "missing")
        self.assertEqual(self.read([self.observation(0)]).value, 0)
        self.assertEqual(self.read([self.observation(0)], 21).status, "stale")
        self.assertEqual(self.read([self.observation(2), self.observation(None, 5, 5)], 5).status,
                         "invalid")

    def test_conflicting_revisions_rejected(self):
        with self.assertRaises(ValueError):
            self.read([self.observation(1), self.observation(2)])

    def test_clock_and_nonfinite_inputs_rejected(self):
        with self.assertRaises(ValueError):
            self.observation(1, observed=2, available=1)
        with self.assertRaises(ValueError):
            self.observation(float("nan"))
        with self.assertRaises(ValueError):
            asof_reading([], "x", "x", "x", "x", datetime(2026, 1, 1), timedelta(0))

    def test_no_silent_session_truncation(self):
        flat = self.t + timedelta(hours=3)
        self.assertTrue(horizon_eligible(self.t, timedelta(0), timedelta(hours=2), self.t, flat))
        self.assertFalse(horizon_eligible(self.t, timedelta(0), timedelta(hours=4), self.t, flat))
        self.assertFalse(horizon_eligible(self.t, timedelta(seconds=1), timedelta(hours=3), self.t, flat))

    def test_all_common_local_sign_cases_reconstruct(self):
        for common in (-4, 0, 4):
            for local in (-6, 0, 6):
                c, e = common_local(common + local, common, 1)
                self.assertEqual((c, e), (common, local))
                self.assertEqual(c + e, common + local)

    def test_curve_reconstruction_and_flattening(self):
        for d2 in (-5, 0, 5):
            for d5 in (-3, 0, 3):
                for d10 in (-2, 0, 2):
                    self.assertEqual(reconstruct_curve(*curve_coordinates(d2, d5, d10)),
                                     (d2, d5, d10))
        self.assertEqual(curve_coordinates(5, 2, 1)[1], -3)
        self.assertEqual(curve_coordinates(-1, -4, -2)[1], -3)

    def test_same_endpoint_different_adverse_path(self):
        smooth = path_outcome([120, 119.96, 119.90], -1)
        rough = path_outcome([120, 120.30, 119.90], -1)
        self.assertAlmostEqual(smooth.endpoint_ticks, rough.endpoint_ticks)
        self.assertAlmostEqual(smooth.mae_ticks, 0)
        self.assertAlmostEqual(rough.mae_ticks, 30)

    def test_path_direction_and_half_ticks(self):
        a = path_outcome([120, 120.005, 119.995], 1)
        b = path_outcome([120, 120.005, 119.995], -1)
        self.assertAlmostEqual(a.endpoint_ticks, -0.5)
        self.assertAlmostEqual(a.endpoint_ticks, -b.endpoint_ticks)
        self.assertAlmostEqual(a.mfe_ticks, b.mae_ticks)
        self.assertAlmostEqual(a.mae_ticks, b.mfe_ticks)

    def test_flat_midpoint_loses_one_spread(self):
        for direction in (-1, 1):
            p = self.pnl(direction)
            self.assertAlmostEqual(p.gross_ticks, -1)
            self.assertAlmostEqual(p.net_cad, -10)

    def test_fees_slippage_and_signs(self):
        up = self.quote(60, bid=120.10, ask=120.11)
        self.assertAlmostEqual(self.pnl(1, exit=up, fee=2, slip=0.5).net_cad, 83)
        self.assertAlmostEqual(self.pnl(-1, exit=up).gross_ticks, -11)

    def test_spread_widening_without_midpoint_move(self):
        wide = self.quote(60, bid=119.99, ask=120.02)
        self.assertAlmostEqual((wide.bid + wide.ask) / 2, 120.005)
        for direction in (-1, 1):
            self.assertAlmostEqual(self.pnl(direction, exit=wide).gross_ticks, -2)

    def test_latency_move_is_not_credited_to_execution(self):
        entry = self.quote(10, bid=120.10, ask=120.11)
        exit = self.quote(70, bid=120.12, ask=120.13)
        p = quote_touch_pnl(1, entry, exit, self.t + timedelta(seconds=10),
                            self.t + timedelta(seconds=70), timedelta(seconds=1),
                            1, 0, 0)
        decision_to_exit = path_outcome([120.005, 120.105, 120.125], 1)
        self.assertAlmostEqual(decision_to_exit.endpoint_ticks, 12)
        self.assertAlmostEqual(p.gross_ticks, 1)

    def test_roll_stale_depth_and_future_quotes_rejected(self):
        bad_exits = [self.quote(60, contract="OTHER"), self.quote(58),
                     self.quote(61), self.quote(60, size=0)]
        for q in bad_exits:
            with self.assertRaises(ValueError):
                self.pnl(1, exit=q)

    def test_pressure_cases_are_assumptions_not_estimators(self):
        self.assertEqual(frozen_pressure_response(-2, 1, 0, 4), -2)
        self.assertEqual(frozen_pressure_response(-2, 1, 1, 4), -8)
        self.assertAlmostEqual(frozen_pressure_response(-2, 1, 0.5, 4), -3.75)
        self.assertEqual(frozen_pressure_response(-2, 0, 0.5, 4), 0)
        self.assertEqual(frozen_pressure_response(-2, 1, -1, 4), 0)
        self.assertEqual(frozen_pressure_response(-2, 1, 2, 4), -30)
        self.assertEqual(frozen_pressure_response(-2, 1, 0.5, 4),
                         frozen_pressure_response(-4, 0.5, 0.5, 4))


if __name__ == "__main__":
    unittest.main(verbosity=2)

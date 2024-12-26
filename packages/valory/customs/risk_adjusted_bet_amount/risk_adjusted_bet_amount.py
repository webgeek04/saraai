# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2024 Valory AG
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
# ------------------------------------------------------------------------------

"""This module calculates a risk-adjusted bet amount based on bankroll, win probability, and risk tolerance."""

from typing import Dict, Any, List, Union, Optional

REQUIRED_FIELDS = frozenset(
    {
        "bet_kelly_fraction", 
        "bankroll", 
        "win_probability", 
        "selected_type_tokens_in_pool", 
        "other_tokens_in_pool", 
        "bet_fee", 
        "floor_balance",
        "risk_tolerance",
    }
)
OPTIONAL_FIELDS = frozenset({"max_bet"})
ALL_FIELDS = REQUIRED_FIELDS.union(OPTIONAL_FIELDS)
DEFAULT_MAX_BET = 8e17


def check_missing_fields(kwargs: Dict[str, Any]) -> List[str]:
    """Check for missing fields and return them, if any."""
    missing = []
    for field in REQUIRED_FIELDS:
        if kwargs.get(field, None) is None:
            missing.append(field)
    return missing


def remove_irrelevant_fields(kwargs: Dict[str, Any]) -> Dict[str, Any]:
    """Remove the irrelevant fields from the given kwargs."""
    return {key: value for key, value in kwargs.items() if key in ALL_FIELDS}


def calculate_risk_adjusted_bet_amount(
    selected_type_tokens_in_pool: int,
    other_tokens_in_pool: int,
    win_probability: float,
    bankroll: int,
    risk_tolerance: float,
    bet_fee: int,
) -> int:
    """Calculate the risk-adjusted bet amount without using the confidence factor."""
    # Calculating Kelly bet without confidence factor, adjusted by risk tolerance
    bankroll_adjusted = bankroll * risk_tolerance  # Adjust bankroll based on risk tolerance
    fee_fraction = 1 - wei_to_native(bet_fee)  # Adjust for bet fee

    if bankroll_adjusted <= 0:
        return 0  # No bet if bankroll adjusted to zero or negative

    kelly_bet_amount = calculate_kelly_bet_amount_no_conf(
        selected_type_tokens_in_pool,
        other_tokens_in_pool,
        win_probability,
        bankroll_adjusted,
        fee_fraction
    )

    return int(kelly_bet_amount)


def wei_to_native(wei: int) -> float:
    """Convert WEI to native token."""
    return wei / 10**18


def get_bet_amount_risk_adjusted(
    bet_kelly_fraction: float,
    bankroll: int,
    win_probability: float,
    selected_type_tokens_in_pool: int,
    other_tokens_in_pool: int,
    bet_fee: int,
    risk_tolerance: float,
    floor_balance: int,
    max_bet: int = DEFAULT_MAX_BET,
) -> Dict[str, Union[int, List[str]]]:
    """Calculate the risk-adjusted bet amount without using the confidence factor."""
    # Keep `floor_balance` in the bankroll
    bankroll_adj = bankroll - floor_balance
    bankroll_adj = min(bankroll_adj, max_bet)
    bankroll_adj_xdai = wei_to_native(bankroll_adj)
    info = [f"Adjusted bankroll: {bankroll_adj_xdai} xDAI."]
    error = []

    if bankroll_adj <= 0:
        error.append(
            f"Bankroll ({bankroll_adj}) is less than the floor balance ({floor_balance})."
        )
        error.append("Set bet amount to 0.")
        error.append("Top up safe with DAI or wait for redeeming.")
        return {"bet_amount": 0, "info": info, "error": error}

    # Calculate the Kelly bet without confidence using risk tolerance
    bet_amount = calculate_risk_adjusted_bet_amount(
        selected_type_tokens_in_pool,
        other_tokens_in_pool,
        win_probability,
        bankroll_adj,
        risk_tolerance,
        bet_fee,
    )

    if bet_amount < 0:
        info.append(f"Invalid bet amount: {bet_amount}. Set bet amount to 0.")
        return {"bet_amount": 0, "info": info, "error": error}

    info.append(f"Risk-adjusted bet amount: {wei_to_native(bet_amount)} xDAI")
    info.append(f"Bet kelly fraction: {bet_kelly_fraction}")
    return {"bet_amount": bet_amount, "info": info, "error": error}


def run(*_args, **kwargs) -> Dict[str, Union[int, List[str]]]:
    """Run the strategy."""
    missing = check_missing_fields(kwargs)
    if len(missing) > 0:
        return {"error": [f"Required kwargs {missing} were not provided."]}
    
    kwargs = remove_irrelevant_fields(kwargs)
    return get_bet_amount_risk_adjusted(**kwargs)

# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2023-2024 Valory AG
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

"""This module calculates the risk-adjusted position size based on the trader's confidence level and risk tolerance."""

from typing import Union, List, Dict, Tuple, Any

REQUIRED_FIELDS = ("confidence", "risk_tolerance", "base_position_size")

def check_missing_fields(kwargs: Dict[str, Any]) -> List[str]:
    """Check for missing fields and return them, if any."""
    missing = []
    for field in REQUIRED_FIELDS:
        if kwargs.get(field, None) is None:
            missing.append(field)
    return missing


def remove_irrelevant_fields(kwargs: Dict[str, Any]) -> Dict[str, Any]:
    """Remove the irrelevant fields from the given kwargs."""
    return {key: value for key, value in kwargs.items() if key in REQUIRED_FIELDS}


def risk_adjusted_position_size(
    confidence: float, risk_tolerance: float, base_position_size: float
) -> Dict[str, Union[float, Tuple[str]]]:
    """Calculate the risk-adjusted position size based on the trader's confidence and risk tolerance."""
    
    # Calculate the position size adjustment factor based on confidence and risk tolerance.
    # The more confident the trader is, the larger the position size, but the risk tolerance 
    # limits the maximum position size.
    adjusted_position_size = base_position_size * (confidence * risk_tolerance)

    # Return the adjusted position size.
    return {"adjusted_position_size": round(adjusted_position_size, 2)}


def run(*_args, **kwargs) -> Dict[str, Union[float, Tuple[str]]]:
    """Run the strategy."""
    missing = check_missing_fields(kwargs)
    if len(missing) > 0:
        return {"error": (f"Required kwargs {missing} were not provided.",)}

    kwargs = remove_irrelevant_fields(kwargs)
    return risk_adjusted_position_size(**kwargs)

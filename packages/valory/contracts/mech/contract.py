# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2023 Valory AG
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

"""This module contains the class to connect to a Mech contract."""

from typing import Dict, Optional, cast, List, Any

from aea.common import JSONLike
from aea.configurations.base import PublicId
from aea.contracts.base import Contract
from aea.crypto.base import LedgerApi
from aea_ledger_ethereum import EthereumApi
from eth_typing import HexStr
from web3.types import TxReceipt, EventData

PUBLIC_ID = PublicId.from_str("valory/mech:0.1.0")


class Mech(Contract):
    """The Mech contract."""

    contract_id = PUBLIC_ID

    @classmethod
    def get_price(
        cls,
        ledger_api: EthereumApi,
        contract_address: str,
    ) -> JSONLike:
        """Get the price of a request."""
        contract_instance = cls.get_instance(ledger_api, contract_address)
        price = ledger_api.contract_method_call(contract_instance, "price")
        return dict(price=price)

    @classmethod
    def get_request_data(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        request_data: bytes,
    ) -> Dict[str, bytes]:
        """Gets the encoded arguments for a request tx, which should only be called via the multisig.

        :param ledger_api: the ledger API object
        :param contract_address: the contract's address
        :param request_data: the request data
        """
        contract_instance = cls.get_instance(ledger_api, contract_address)
        encoded_data = contract_instance.encodeABI("request", request_data)
        return {"data": bytes.fromhex(encoded_data[2:])}

    @classmethod
    def _process_event(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        tx_hash: HexStr,
        event_name: str,
        *args: Any,
    ) -> Optional[JSONLike]:
        """Process the logs of the given event."""
        ledger_api = cast(EthereumApi, ledger_api)
        contract = cls.get_instance(ledger_api, contract_address)
        receipt: TxReceipt = ledger_api.api.eth.get_transaction_receipt(tx_hash)
        event_method = getattr(contract.events, event_name)
        logs: List[EventData] = list(event_method().processReceipt(receipt))

        n_logs = len(logs)
        if n_logs != 1:
            error = f"A single {event_name!r} event was expected. tx {tx_hash} emitted {n_logs} instead."
            return {"error": error}

        log = logs.pop()
        event_args = log.get("args", None)
        if event_args is None or (
            expected_key not in event_args for expected_key in args
        ):
            error = f"The emitted event's ({event_name!r}) log for tx {tx_hash} do not match the expected format: {log}"
            return {"error": error}

        return {arg_name: event_args[arg_name] for arg_name in args}

    @classmethod
    def process_request_event(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        tx_hash: HexStr,
    ) -> Optional[JSONLike]:
        """
        Process the request receipt to get the requestId and the given data from the `Request` event's logs.

        :param ledger_api: the ledger apis.
        :param contract_address: the contract address.
        :param tx_hash: the hash of a request tx to be processed.
        :return: a dictionary with the request id.
        """
        return cls._process_event(
            ledger_api, contract_address, tx_hash, "Request", "requestId", "data"
        )

    @classmethod
    def process_deliver_event(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        tx_hash: HexStr,
    ) -> Optional[JSONLike]:
        """
        Process the request receipt to get the requestId and the delivered data if the `Deliver` event has been emitted.

        :param ledger_api: the ledger apis.
        :param contract_address: the contract address.
        :param tx_hash: the hash of a request tx to be processed.
        :return: a dictionary with the request id and the data.
        """
        return cls._process_event(
            ledger_api, contract_address, tx_hash, "Deliver", "requestId", "data"
        )
from decimal import Decimal
from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest

from app.services.currency import CurrencyService, CurrencyServiceError


@pytest.mark.asyncio
async def test_normalizes_nbrb_rate_for_scale() -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200,
            json={"Cur_Scale": 100, "Cur_OfficialRate": 3.25},
        )
    )
    assert await CurrencyService(transport).get_rub_to_byn_rate() == Decimal("0.0325")


@pytest.mark.asyncio
async def test_scale_one() -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200,
            json={"Cur_Scale": 1, "Cur_OfficialRate": 0.03},
        )
    )
    assert await CurrencyService(transport).get_rub_to_byn_rate() == Decimal("0.03")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"Cur_Scale": 0, "Cur_OfficialRate": 3},
        {"Cur_Scale": 100, "Cur_OfficialRate": None},
    ],
)
async def test_invalid_response(payload: dict) -> None:
    transport = httpx.MockTransport(lambda request: httpx.Response(200, json=payload))
    with pytest.raises(CurrencyServiceError):
        await CurrencyService(transport).get_rub_to_byn_rate()


@pytest.mark.asyncio
async def test_http_error() -> None:
    transport = httpx.MockTransport(lambda request: httpx.Response(503))
    with pytest.raises(CurrencyServiceError):
        await CurrencyService(transport).get_rub_to_byn_rate()


@pytest.mark.asyncio
async def test_default_client_ignores_environment_proxies() -> None:
    response = Mock()
    response.json.return_value = {"Cur_Scale": 100, "Cur_OfficialRate": 3.5}
    client = AsyncMock()
    client.__aenter__.return_value = client
    client.get.return_value = response

    with patch("app.services.currency.httpx.AsyncClient", return_value=client) as client_class:
        assert await CurrencyService(timeout=7.0).get_rub_to_byn_rate() == Decimal("0.035")

    client_class.assert_called_once_with(timeout=7.0, trust_env=False, transport=None)

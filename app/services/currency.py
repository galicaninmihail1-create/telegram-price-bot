from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

import httpx


class CurrencyServiceError(RuntimeError):
    """The official exchange rate could not be obtained or validated."""


@dataclass(frozen=True, slots=True)
class RubRate:
    scale: Decimal
    official_rate: Decimal

    @property
    def per_one_rub(self) -> Decimal:
        return self.official_rate / self.scale


class CurrencyService:
    URL = "https://api.nbrb.by/exrates/rates/RUB?parammode=2"

    def __init__(self, transport: httpx.AsyncBaseTransport | None = None, timeout: float = 10.0) -> None:
        self._transport = transport
        self._timeout = timeout

    async def get_rub_rate(self) -> RubRate:
        try:
            async with httpx.AsyncClient(
                timeout=self._timeout,
                trust_env=False,
                transport=self._transport,
            ) as client:
                response = await client.get(self.URL)
                response.raise_for_status()
                payload = response.json()
            rate = RubRate(
                scale=Decimal(str(payload["Cur_Scale"])),
                official_rate=Decimal(str(payload["Cur_OfficialRate"])),
            )
            if rate.scale <= 0 or rate.official_rate <= 0:
                raise ValueError("non-positive rate")
            return rate
        except (httpx.HTTPError, KeyError, TypeError, ValueError, InvalidOperation) as exc:
            raise CurrencyServiceError("Не удалось получить актуальный курс RUB/BYN") from exc

    async def get_rub_to_byn_rate(self) -> Decimal:
        return (await self.get_rub_rate()).per_one_rub

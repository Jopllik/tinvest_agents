from typing import List, Dict, Optional
from dataclasses import dataclass
import json
from pathlib import Path

from core.client import invest_client


def quotation_to_float(q) -> float:
    if q is None:
        return 0.0
    return float(q.units) + float(q.nano) / 1_000_000_000


@dataclass
class TradableShare:
    figi: str
    ticker: str
    name: str
    lot: int
    currency: str
    class_code: str
    last_price: float = 0.0


def get_filtered_shares(min_price: float = 5.0, max_price: float = 1000.0) -> List[TradableShare]:
    """
    Акции:
    - доступны неквалифицированным (for_qual_investor_flag = False)
    - без обязательных тестов
    - api_trade_available = True
    - buy_available = True
    - валюта RUB
    - class_code = TQBR
    - текущая цена < max_price
    """
    result = []

    with invest_client.get_client() as client:
        # 1. Получаем все акции
        response = client.instruments.shares()
        
        candidates = []
        for share in response.instruments:
            if not share.api_trade_available_flag:
                continue
            if share.for_qual_investor_flag:
                continue
            if share.required_tests:
                continue
            if not share.buy_available_flag:
                continue
            if share.currency.upper() != "RUB":
                continue
            if share.class_code != "TQBR":
                continue

            candidates.append(share)

        print(f"Кандидатов после базовых фильтров: {len(candidates)}")

        if not candidates:
            return []

        # 2. Получаем последние цены (можно пачками)
        figis = [s.figi for s in candidates]
        
        # API позволяет передавать список figi
        last_prices_resp = client.market_data.get_last_prices(figi=figis)
        price_map = {
            p.figi: quotation_to_float(p.price)
            for p in last_prices_resp.last_prices
        }

        # 3. Фильтруем по цене
        for share in candidates:
            price = price_map.get(share.figi, 0.0)
            if min_price <= price < max_price:
                result.append(TradableShare(
                    figi=share.figi,
                    ticker=share.ticker,
                    name=share.name,
                    lot=share.lot,
                    currency=share.currency,
                    class_code=share.class_code,
                    last_price=price
                ))

    # Сортируем по цене (от дешёвых к дорогим)
    result.sort(key=lambda x: x.last_price)
    return result


def save_shares(shares: List[TradableShare], filename: str = "filtered_shares.json"):
    data = [
        {
            "figi": s.figi,
            "ticker": s.ticker,
            "name": s.name,
            "lot": s.lot,
            "last_price": round(s.last_price, 2)
        }
        for s in shares
    ]
    Path(filename).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Сохранено {len(data)} акций в {filename}")


def load_shares_from_file(filename: str = "filtered_shares.json") -> List[Dict]:
    path = Path(filename)
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))
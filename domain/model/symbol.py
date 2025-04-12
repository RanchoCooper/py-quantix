from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class SymbolFilter:
    filter_type: str
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    tick_size: Optional[float] = None
    min_qty: Optional[float] = None
    max_qty: Optional[float] = None
    step_size: Optional[float] = None
    min_notional: Optional[float] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SymbolFilter":
        filter_type = data["filterType"]
        result = cls(filter_type=filter_type)

        if filter_type == "PRICE_FILTER":
            result.min_price = float(data.get("minPrice", 0))
            result.max_price = float(data.get("maxPrice", 0))
            result.tick_size = float(data.get("tickSize", 0))
        elif filter_type == "LOT_SIZE":
            result.min_qty = float(data.get("minQty", 0))
            result.max_qty = float(data.get("maxQty", 0))
            result.step_size = float(data.get("stepSize", 0))
        elif filter_type == "MIN_NOTIONAL":
            result.min_notional = float(data.get("minNotional", 0))

        return result


@dataclass
class Symbol:
    symbol: str
    base_asset: str
    quote_asset: str
    status: str
    filters: List[SymbolFilter]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Symbol":
        return cls(
            symbol=data["symbol"],
            base_asset=data["baseAsset"],
            quote_asset=data["quoteAsset"],
            status=data["status"],
            filters=[SymbolFilter.from_dict(f) for f in data.get("filters", [])],
        )

    def get_filter(self, filter_type: str) -> Optional[SymbolFilter]:
        """Get a specific filter by type."""
        for f in self.filters:
            if f.filter_type == filter_type:
                return f
        return None

    def get_price_precision(self) -> int:
        """Get price precision from tick size."""
        price_filter = self.get_filter("PRICE_FILTER")
        if price_filter and price_filter.tick_size:
            tick_size_str = str(price_filter.tick_size)
            if "." in tick_size_str:
                return len(tick_size_str.split(".")[1].rstrip("0"))
        return 8  # Default precision

    def get_quantity_precision(self) -> int:
        """Get quantity precision from step size."""
        lot_size = self.get_filter("LOT_SIZE")
        if lot_size and lot_size.step_size:
            step_size_str = str(lot_size.step_size)
            if "." in step_size_str:
                return len(step_size_str.split(".")[1].rstrip("0"))
        return 8  # Default precision

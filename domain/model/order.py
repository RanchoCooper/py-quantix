from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class OrderFill:
    price: float
    quantity: float
    commission: float
    commission_asset: str
    trade_id: int


@dataclass
class Order:
    symbol: str
    order_id: int
    client_order_id: str
    price: float
    orig_qty: float
    executed_qty: float
    status: str
    time_in_force: str
    type: str
    side: str
    stop_price: Optional[float] = None
    iceberg_qty: Optional[float] = None
    time: Optional[datetime] = None
    update_time: Optional[datetime] = None
    is_working: bool = True
    orig_quote_order_qty: float = 0.0
    fills: List[OrderFill] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Order":
        fills = []
        if "fills" in data and data["fills"]:
            for fill_data in data["fills"]:
                fills.append(
                    OrderFill(
                        price=float(fill_data["price"]),
                        quantity=float(fill_data["qty"]),
                        commission=float(fill_data["commission"]),
                        commission_asset=fill_data["commissionAsset"],
                        trade_id=int(fill_data["tradeId"]),
                    )
                )

        # Convert timestamps to datetime objects if present
        time = None
        if "time" in data and data["time"]:
            time = datetime.fromtimestamp(int(data["time"]) / 1000)

        update_time = None
        if "updateTime" in data and data["updateTime"]:
            update_time = datetime.fromtimestamp(int(data["updateTime"]) / 1000)

        return cls(
            symbol=data["symbol"],
            order_id=int(data["orderId"]),
            client_order_id=data["clientOrderId"],
            price=float(data["price"]),
            orig_qty=float(data["origQty"]),
            executed_qty=float(data.get("executedQty", 0)),
            status=data["status"],
            time_in_force=data["timeInForce"],
            type=data["type"],
            side=data["side"],
            stop_price=float(data["stopPrice"])
            if "stopPrice" in data and data["stopPrice"]
            else None,
            iceberg_qty=float(data["icebergQty"])
            if "icebergQty" in data and data["icebergQty"]
            else None,
            time=time,
            update_time=update_time,
            is_working=data.get("isWorking", True),
            orig_quote_order_qty=float(data.get("origQuoteOrderQty", 0)),
            fills=fills,
        )

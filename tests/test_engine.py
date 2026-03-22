"""
Engine 层测试：开仓 / 平仓 / 价格更新 / 风控
"""
import pytest
import pytest_asyncio

from paper_trading.service import PaperTradingService
from paper_trading.config import PaperTradingConfig
from paper_trading.feishu_integration import init_feishu_integration


class TestOpenPosition:
    """开仓测试"""

    @pytest.mark.asyncio
    async def test_open_long_position_success(self, fresh_db):
        """开多仓：验证保证金冻结、手续费扣除"""
        from paper_trading.service import PaperTradingService

        svc = PaperTradingService(PaperTradingConfig(confirm_via_feishu=False))
        account = await svc.create_account("test", 10000.0, 10)

        result = await svc.engine.open_position(
            account_id=account.id,
            symbol="BTCUSDT",
            side="long",
            quantity=0.01,
            entry_price=95000.0,
        )

        assert result["success"] is True
        position = result["position"]
        assert position.symbol == "BTCUSDT"
        assert position.side == "long"
        assert position.quantity == 0.01
        assert position.entry_price == 95000.0

        # 验证保证金冻结
        margin = 0.01 * 95000.0 / 10  # 95.0
        fee = 0.01 * 95000.0 * 0.0004  # 0.38
        assert result["margin_used"] == pytest.approx(margin, abs=0.01)
        assert result["fee"] == pytest.approx(fee, abs=0.01)

        # 验证账户余额更新
        updated = await svc.get_account(account.id)
        assert updated.balance == pytest.approx(10000.0 - margin - fee, abs=0.01)
        assert updated.frozen_margin == pytest.approx(margin, abs=0.01)

    @pytest.mark.asyncio
    async def test_open_short_position_success(self, fresh_db):
        """开空仓：验证保证金冻结"""
        svc = PaperTradingService(PaperTradingConfig(confirm_via_feishu=False))
        account = await svc.create_account("test", 10000.0, 10)

        result = await svc.engine.open_position(
            account_id=account.id,
            symbol="ETHUSDT",
            side="short",
            quantity=0.1,
            entry_price=3000.0,
        )

        assert result["success"] is True
        position = result["position"]
        assert position.side == "short"
        assert position.symbol == "ETHUSDT"

    @pytest.mark.asyncio
    async def test_open_position_insufficient_balance(self, fresh_db):
        """保证金不足时拒绝开仓"""
        svc = PaperTradingService(PaperTradingConfig(confirm_via_feishu=False))
        account = await svc.create_account("test", 100.0, 10)

        # 需要保证金 = 0.01 * 105000 / 10 = 105 > 账户余额 100
        result = await svc.engine.open_position(
            account_id=account.id,
            symbol="BTCUSDT",
            side="long",
            quantity=0.01,
            entry_price=105000.0,
        )

        assert result["success"] is False
        assert "保证金不足" in result["error"]

    @pytest.mark.asyncio
    async def test_open_position_with_stop_loss_take_profit(self, fresh_db):
        """开仓时设置止损止盈"""
        svc = PaperTradingService(PaperTradingConfig(confirm_via_feishu=False))
        account = await svc.create_account("test", 10000.0, 10)

        result = await svc.engine.open_position(
            account_id=account.id,
            symbol="BTCUSDT",
            side="long",
            quantity=0.01,
            entry_price=95000.0,
            stop_loss=94000.0,
            take_profit=97000.0,
        )

        assert result["success"] is True
        position = result["position"]
        assert position.stop_loss == 94000.0
        assert position.take_profit == 97000.0

    @pytest.mark.asyncio
    async def test_open_position_nonexistent_account(self, fresh_db):
        """账户不存在时返回错误"""
        svc = PaperTradingService(PaperTradingConfig(confirm_via_feishu=False))

        result = await svc.engine.open_position(
            account_id="nonexistent-id",
            symbol="BTCUSDT",
            side="long",
            quantity=0.01,
            entry_price=95000.0,
        )

        assert result["success"] is False
        assert "账户不存在" in result["error"]


class TestClosePosition:
    """平仓测试"""

    @pytest.mark.asyncio
    async def test_close_long_position_profit(self, fresh_db):
        """多头平仓盈利：验证盈亏计算正确"""
        svc = PaperTradingService(PaperTradingConfig(confirm_via_feishu=False))
        account = await svc.create_account("test", 10000.0, 10)

        # 开多仓
        open_result = await svc.engine.open_position(
            account_id=account.id,
            symbol="BTCUSDT",
            side="long",
            quantity=0.01,
            entry_price=95000.0,
        )
        position_id = open_result["position"].id

        # 平仓（价格上涨）
        close_result = await svc.engine.close_position(
            position_id=position_id,
            exit_price=96000.0,
        )

        assert close_result["success"] is True
        assert close_result["is_full_close"] is True

        # 盈利 = (96000 - 95000) * 0.01 - fee = 10 - fee
        fee = 0.01 * 96000.0 * 0.0004
        expected_pnl = (96000.0 - 95000.0) * 0.01 - fee
        assert close_result["pnl"] == pytest.approx(expected_pnl, abs=0.01)
        assert close_result["fee"] == pytest.approx(fee, abs=0.01)

        # 验证账户余额恢复
        updated = await svc.get_account(account.id)
        assert updated.frozen_margin == 0.0
        # 余额 = 10000 - margin - open_fee + margin + pnl = 10000 + pnl - open_fee

    @pytest.mark.asyncio
    async def test_close_short_position_profit(self, fresh_db):
        """空头平仓盈利（价格下跌）"""
        svc = PaperTradingService(PaperTradingConfig(confirm_via_feishu=False))
        account = await svc.create_account("test", 10000.0, 10)

        # 开空仓
        open_result = await svc.engine.open_position(
            account_id=account.id,
            symbol="BTCUSDT",
            side="short",
            quantity=0.01,
            entry_price=95000.0,
        )
        position_id = open_result["position"].id

        # 平仓（价格下跌）
        close_result = await svc.engine.close_position(
            position_id=position_id,
            exit_price=94000.0,
        )

        assert close_result["success"] is True
        # 空头盈利 = (95000 - 94000) * 0.01 - fee = 10 - fee
        fee = 0.01 * 94000.0 * 0.0004
        expected_pnl = (95000.0 - 94000.0) * 0.01 - fee
        assert close_result["pnl"] == pytest.approx(expected_pnl, abs=0.01)

    @pytest.mark.asyncio
    async def test_close_position_loss(self, fresh_db):
        """多头平仓亏损"""
        svc = PaperTradingService(PaperTradingConfig(confirm_via_feishu=False))
        account = await svc.create_account("test", 10000.0, 10)

        open_result = await svc.engine.open_position(
            account_id=account.id,
            symbol="BTCUSDT",
            side="long",
            quantity=0.01,
            entry_price=95000.0,
        )
        position_id = open_result["position"].id

        close_result = await svc.engine.close_position(
            position_id=position_id,
            exit_price=94000.0,
        )

        assert close_result["success"] is True
        assert close_result["pnl"] < 0

    @pytest.mark.asyncio
    async def test_partial_close(self, fresh_db):
        """部分平仓"""
        svc = PaperTradingService(PaperTradingConfig(confirm_via_feishu=False))
        account = await svc.create_account("test", 10000.0, 10)

        open_result = await svc.engine.open_position(
            account_id=account.id,
            symbol="BTCUSDT",
            side="long",
            quantity=0.01,
            entry_price=95000.0,
        )
        position_id = open_result["position"].id

        close_result = await svc.engine.close_position(
            position_id=position_id,
            quantity=0.005,  # 平一半
            exit_price=96000.0,
        )

        assert close_result["success"] is True
        assert close_result["is_full_close"] is False

        # 验证剩余持仓
        remaining = await svc.engine.update_position_prices(
            account.id, {"BTCUSDT": 96000.0}
        )
        assert len(remaining) == 1
        assert remaining[0]["symbol"] == "BTCUSDT"

    @pytest.mark.asyncio
    async def test_close_nonexistent_position(self, fresh_db):
        """平不存在的持仓"""
        svc = PaperTradingService(PaperTradingConfig(confirm_via_feishu=False))
        result = await svc.engine.close_position(
            position_id="nonexistent",
            exit_price=96000.0,
        )
        assert result["success"] is False
        assert "持仓不存在" in result["error"]

    @pytest.mark.asyncio
    async def test_close_with_no_exit_price(self, fresh_db):
        """平仓未提供价格时返回错误"""
        svc = PaperTradingService(PaperTradingConfig(confirm_via_feishu=False))
        account = await svc.create_account("test", 10000.0, 10)
        open_result = await svc.engine.open_position(
            account_id=account.id,
            symbol="BTCUSDT",
            side="long",
            quantity=0.01,
            entry_price=95000.0,
        )

        result = await svc.engine.close_position(
            position_id=open_result["position"].id,
            exit_price=None,
        )
        assert result["success"] is False
        assert "价格不能为空" in result["error"]


class TestPositionPriceUpdate:
    """持仓价格更新测试"""

    @pytest.mark.asyncio
    async def test_update_price_long_profit(self, fresh_db):
        """多头持仓价格上涨：浮动盈亏增加"""
        svc = PaperTradingService(PaperTradingConfig(confirm_via_feishu=False))
        account = await svc.create_account("test", 10000.0, 10)

        await svc.engine.open_position(
            account_id=account.id,
            symbol="BTCUSDT",
            side="long",
            quantity=0.01,
            entry_price=95000.0,
        )

        updated = await svc.engine.update_position_prices(
            account.id, {"BTCUSDT": 96000.0}
        )

        assert len(updated) == 1
        assert updated[0]["symbol"] == "BTCUSDT"
        # 浮动盈亏 = (96000 - 95000) * 0.01 = 10
        assert updated[0]["unrealized_pnl"] == pytest.approx(10.0, abs=0.01)
        assert updated[0]["unrealized_pnl_pct"] > 0

    @pytest.mark.asyncio
    async def test_update_price_short_profit(self, fresh_db):
        """空头持仓价格下跌：浮动盈亏增加"""
        svc = PaperTradingService(PaperTradingConfig(confirm_via_feishu=False))
        account = await svc.create_account("test", 10000.0, 10)

        await svc.engine.open_position(
            account_id=account.id,
            symbol="BTCUSDT",
            side="short",
            quantity=0.01,
            entry_price=95000.0,
        )

        updated = await svc.engine.update_position_prices(
            account.id, {"BTCUSDT": 94000.0}
        )

        assert len(updated) == 1
        assert updated[0]["unrealized_pnl"] > 0

    @pytest.mark.asyncio
    async def test_update_multiple_positions(self, fresh_db):
        """批量更新多个持仓价格"""
        svc = PaperTradingService(PaperTradingConfig(confirm_via_feishu=False))
        account = await svc.create_account("test", 10000.0, 10)

        await svc.engine.open_position(
            account_id=account.id,
            symbol="BTCUSDT",
            side="long",
            quantity=0.01,
            entry_price=95000.0,
        )
        await svc.engine.open_position(
            account_id=account.id,
            symbol="ETHUSDT",
            side="short",
            quantity=0.1,
            entry_price=3000.0,
        )

        updated = await svc.engine.update_position_prices(
            account.id,
            {"BTCUSDT": 96000.0, "ETHUSDT": 2900.0}
        )

        assert len(updated) == 2
        symbols = {u["symbol"] for u in updated}
        assert symbols == {"BTCUSDT", "ETHUSDT"}


class TestRiskControl:
    """风控测试"""

    @pytest.mark.asyncio
    async def test_risk_check_insufficient_balance(self, fresh_db):
        """风控检查：保证金不足"""
        svc = PaperTradingService(PaperTradingConfig(confirm_via_feishu=False))
        account = await svc.create_account("test", 100.0, 10)

        margin_needed = 100.0  # 需要刚好等于余额
        passed, msg = await svc.engine.risk_check(account.id, margin_needed)
        assert passed is True  # 刚好够

        margin_needed = 100.01
        passed, msg = await svc.engine.risk_check(account.id, margin_needed)
        assert passed is False
        assert "保证金不足" in msg

    @pytest.mark.asyncio
    async def test_risk_check_nonexistent_account(self, fresh_db):
        """风控检查：账户不存在"""
        svc = PaperTradingService(PaperTradingConfig(confirm_via_feishu=False))
        passed, msg = await svc.engine.risk_check("nonexistent", 100.0)
        assert passed is False
        assert "账户不存在" in msg

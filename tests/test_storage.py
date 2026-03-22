"""
Storage 层测试：账户 / 持仓 / 订单 / 信号 CRUD
"""
import pytest
import pytest_asyncio

from paper_trading.service import PaperTradingService
from paper_trading.config import PaperTradingConfig


class TestAccountCRUD:
    """账户 CRUD 测试"""

    @pytest.mark.asyncio
    async def test_create_account(self, fresh_db):
        """创建账户：验证字段正确"""
        from paper_trading.service import PaperTradingService
        svc = PaperTradingService(PaperTradingConfig(confirm_via_feishu=False))
        account = await svc.create_account("Test Account", 10000.0, 10)

        assert account.name == "Test Account"
        assert account.initial_balance == 10000.0
        assert account.balance == 10000.0
        assert account.frozen_margin == 0.0
        assert account.leverage == 10
        assert account.total_pnl == 0.0
        assert account.id is not None

    @pytest.mark.asyncio
    async def test_get_account(self, fresh_db):
        """获取账户"""
        from paper_trading.service import PaperTradingService
        svc = PaperTradingService(PaperTradingConfig(confirm_via_feishu=False))
        created = await svc.create_account("Test Account", 10000.0, 10)
        fetched = await svc.get_account(created.id)

        assert fetched is not None
        assert fetched.id == created.id
        assert fetched.name == created.name

    @pytest.mark.asyncio
    async def test_get_nonexistent_account(self, fresh_db):
        """获取不存在的账户"""
        from paper_trading.service import PaperTradingService
        svc = PaperTradingService(PaperTradingConfig(confirm_via_feishu=False))
        fetched = await svc.get_account("nonexistent-id")
        assert fetched is None

    @pytest.mark.asyncio
    async def test_list_accounts(self, fresh_db):
        """账户列表"""
        from paper_trading.service import PaperTradingService
        svc = PaperTradingService(PaperTradingConfig(confirm_via_feishu=False))
        await svc.create_account("Account 1", 10000.0, 10)
        await svc.create_account("Account 2", 20000.0, 5)

        accounts = await svc.list_accounts()
        assert len(accounts) == 2

    @pytest.mark.asyncio
    async def test_update_account(self, fresh_db):
        """更新账户"""
        from paper_trading.service import PaperTradingService
        svc = PaperTradingService(PaperTradingConfig(confirm_via_feishu=False))
        account = await svc.create_account("Original", 10000.0, 10)

        updated = await svc.update_account(account.id, name="Updated", leverage=20)
        assert updated.name == "Updated"
        assert updated.leverage == 20

    @pytest.mark.asyncio
    async def test_delete_account(self, fresh_db):
        """删除账户"""
        from paper_trading.service import PaperTradingService
        svc = PaperTradingService(PaperTradingConfig(confirm_via_feishu=False))
        account = await svc.create_account("To Delete", 10000.0, 10)

        ok = await svc.delete_account(account.id)
        assert ok is True

        fetched = await svc.get_account(account.id)
        assert fetched is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_account(self, fresh_db):
        """删除不存在的账户"""
        from paper_trading.service import PaperTradingService
        svc = PaperTradingService(PaperTradingConfig(confirm_via_feishu=False))
        ok = await svc.delete_account("nonexistent")
        assert ok is False

    @pytest.mark.asyncio
    async def test_account_available_balance(self, fresh_db):
        """账户可用余额计算"""
        from paper_trading.service import PaperTradingService
        svc = PaperTradingService(PaperTradingConfig(confirm_via_feishu=False))
        account = await svc.create_account("Test", 10000.0, 10)

        # 可用 = 余额 - 冻结
        assert account.available_balance == 10000.0

        # 开仓冻结保证金
        await svc.engine.open_position(
            account_id=account.id,
            symbol="BTCUSDT",
            side="long",
            quantity=0.01,
            entry_price=95000.0,
        )

        updated = await svc.get_account(account.id)
        # fee = 0.01 * 95000 * 0.0004 = 0.38
        # new_balance = 10000 - 95 - 0.38 = 9904.62
        # available = balance - frozen = 9904.62 - 95 = 9809.62
        assert updated.balance == pytest.approx(9904.62, abs=0.01)
        assert updated.frozen_margin == pytest.approx(95.0, abs=0.01)
        assert updated.available_balance == pytest.approx(9809.62, abs=0.01)


class TestPositionCRUD:
    """持仓 CRUD 测试"""

    @pytest.mark.asyncio
    async def test_get_positions_empty(self, fresh_db):
        """空账户无持仓"""
        from paper_trading.service import PaperTradingService
        svc = PaperTradingService(PaperTradingConfig(confirm_via_feishu=False))
        account = await svc.create_account("Test", 10000.0, 10)

        positions = await svc.get_positions(account.id)
        assert len(positions) == 0

    @pytest.mark.asyncio
    async def test_update_position_stop_loss_take_profit(self, fresh_db):
        """更新持仓止损止盈"""
        from paper_trading.service import PaperTradingService
        svc = PaperTradingService(PaperTradingConfig(confirm_via_feishu=False))
        account = await svc.create_account("Test", 10000.0, 10)

        open_result = await svc.engine.open_position(
            account_id=account.id,
            symbol="BTCUSDT",
            side="long",
            quantity=0.01,
            entry_price=95000.0,
        )
        position_id = open_result["position"].id

        updated = await svc.update_position(
            position_id=position_id,
            stop_loss=94000.0,
            take_profit=97000.0,
        )

        assert updated.stop_loss == 94000.0
        assert updated.take_profit == 97000.0

    @pytest.mark.asyncio
    async def test_force_close_position(self, fresh_db):
        """强制平仓"""
        from paper_trading.service import PaperTradingService
        svc = PaperTradingService(PaperTradingConfig(confirm_via_feishu=False))
        account = await svc.create_account("Test", 10000.0, 10)

        open_result = await svc.engine.open_position(
            account_id=account.id,
            symbol="BTCUSDT",
            side="long",
            quantity=0.01,
            entry_price=95000.0,
        )
        position_id = open_result["position"].id

        result = await svc.force_close_position(
            position_id=position_id,
            exit_price=96000.0,
        )

        assert result["success"] is True

        # 验证持仓已删除
        positions = await svc.get_positions(account.id)
        assert len(positions) == 0


class TestOrderCRUD:
    """订单 CRUD 测试"""

    @pytest.mark.asyncio
    async def test_list_orders_empty(self, fresh_db):
        """空账户无订单"""
        from paper_trading.service import PaperTradingService
        svc = PaperTradingService(PaperTradingConfig(confirm_via_feishu=False))
        account = await svc.create_account("Test", 10000.0, 10)

        result = await svc.list_orders(account.id)
        assert result.total == 0
        assert len(result.items) == 0

    @pytest.mark.asyncio
    async def test_orders_pagination(self, fresh_db):
        """订单分页"""
        from paper_trading.service import PaperTradingService
        svc = PaperTradingService(PaperTradingConfig(confirm_via_feishu=False))
        account = await svc.create_account("Test", 10000.0, 10)

        # 创建多笔订单
        for i in range(25):
            await svc.engine.open_position(
                account_id=account.id,
                symbol="BTCUSDT",
                side="long",
                quantity=0.001,
                entry_price=95000.0 + i * 100,
            )

        # 第一页
        page1 = await svc.list_orders(account.id, page=1, page_size=10)
        assert page1.total == 25
        assert len(page1.items) == 10
        assert page1.total_pages == 3

        # 第二页
        page2 = await svc.list_orders(account.id, page=2, page_size=10)
        assert len(page2.items) == 10

        # 第三页
        page3 = await svc.list_orders(account.id, page=3, page_size=10)
        assert len(page3.items) == 5


class TestSignal:
    """信号测试"""

    @pytest.mark.asyncio
    async def test_create_signal(self, fresh_db):
        """创建信号"""
        from paper_trading.service import PaperTradingService
        svc = PaperTradingService(PaperTradingConfig(confirm_via_feishu=False))

        signal = await svc.create_signal(
            symbol="BTCUSDT",
            signal_type="buy",
            entry_price=95000.0,
            stop_loss=94000.0,
            take_profit=97000.0,
            reason="Test signal",
            timeframe="1h",
        )

        assert signal.symbol == "BTCUSDT"
        assert signal.signal_type == "buy"
        assert signal.entry_price == 95000.0
        assert signal.stop_loss == 94000.0
        assert signal.take_profit == 97000.0
        assert signal.status == "pending"

    @pytest.mark.asyncio
    async def test_list_pending_signals(self, fresh_db):
        """待确认信号列表"""
        from paper_trading.service import PaperTradingService
        svc = PaperTradingService(PaperTradingConfig(confirm_via_feishu=False))

        await svc.create_signal(symbol="BTCUSDT", signal_type="buy")
        await svc.create_signal(symbol="ETHUSDT", signal_type="sell")

        pending = await svc.list_pending_signals()
        assert len(pending) == 2

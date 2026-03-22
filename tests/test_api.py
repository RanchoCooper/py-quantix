"""
API 层测试：FastAPI 端点集成测试
"""
import pytest


class TestAccountAPI:
    """账户 API 测试"""

    def test_create_account(self, api_client):
        """创建账户"""
        response = api_client.post(
            "/api/accounts",
            json={"name": "API Test", "initial_balance": 10000.0, "leverage": 10},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "API Test"
        assert data["balance"] == 10000.0
        assert data["frozen_margin"] == 0.0
        assert data["leverage"] == 10

    def test_create_account_validation(self, api_client):
        """创建账户参数验证"""
        # 名称为空
        response = api_client.post(
            "/api/accounts",
            json={"name": "", "initial_balance": 10000.0, "leverage": 10},
        )
        assert response.status_code == 422

        # 初始资金为负
        response = api_client.post(
            "/api/accounts",
            json={"name": "Test", "initial_balance": -100.0, "leverage": 10},
        )
        assert response.status_code == 422

    def test_list_accounts(self, api_client):
        """账户列表"""
        # 先创建
        api_client.post("/api/accounts", json={"name": "Acc1", "initial_balance": 10000.0, "leverage": 10})
        api_client.post("/api/accounts", json={"name": "Acc2", "initial_balance": 20000.0, "leverage": 5})

        response = api_client.get("/api/accounts")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_get_account(self, api_client):
        """获取账户详情"""
        create_resp = api_client.post(
            "/api/accounts",
            json={"name": "Test", "initial_balance": 10000.0, "leverage": 10},
        )
        account_id = create_resp.json()["id"]

        response = api_client.get(f"/api/accounts/{account_id}")
        assert response.status_code == 200
        assert response.json()["id"] == account_id

    def test_get_nonexistent_account(self, api_client):
        """获取不存在的账户"""
        response = api_client.get("/api/accounts/nonexistent-id")
        assert response.status_code == 404

    def test_update_account(self, api_client):
        """更新账户"""
        create_resp = api_client.post(
            "/api/accounts",
            json={"name": "Original", "initial_balance": 10000.0, "leverage": 10},
        )
        account_id = create_resp.json()["id"]

        response = api_client.put(
            f"/api/accounts/{account_id}",
            json={"name": "Updated", "leverage": 20},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated"
        assert data["leverage"] == 20

    def test_delete_account(self, api_client):
        """删除账户"""
        create_resp = api_client.post(
            "/api/accounts",
            json={"name": "ToDelete", "initial_balance": 10000.0, "leverage": 10},
        )
        account_id = create_resp.json()["id"]

        response = api_client.delete(f"/api/accounts/{account_id}")
        assert response.status_code == 200
        assert response.json()["success"] is True

        # 验证已删除
        get_resp = api_client.get(f"/api/accounts/{account_id}")
        assert get_resp.status_code == 404

    def test_delete_nonexistent_account(self, api_client):
        """删除不存在的账户"""
        response = api_client.delete("/api/accounts/nonexistent")
        assert response.status_code == 404


class TestPositionAPI:
    """持仓 API 测试"""

    def test_list_positions_empty(self, api_client):
        """空账户无持仓"""
        create_resp = api_client.post(
            "/api/accounts",
            json={"name": "Test", "initial_balance": 10000.0, "leverage": 10},
        )
        account_id = create_resp.json()["id"]

        response = api_client.get(f"/api/accounts/{account_id}/positions")
        assert response.status_code == 200
        assert response.json() == []

    def test_list_positions_nonexistent_account(self, api_client):
        """不存在的账户返回 404"""
        response = api_client.get("/api/accounts/nonexistent/positions")
        assert response.status_code == 404

    def test_update_position_stop_loss(self, api_client):
        """更新持仓止损止盈"""
        # 创建账户
        create_resp = api_client.post(
            "/api/accounts",
            json={"name": "Test", "initial_balance": 10000.0, "leverage": 10},
        )
        account_id = create_resp.json()["id"]

        # 开仓（confirm_via_feishu=False 时直接执行）
        order_resp = api_client.post(
            "/api/orders",
            json={
                "account_id": account_id,
                "symbol": "BTCUSDT",
                "side": "buy",
                "position_side": "long",
                "quantity": 0.01,
                "price": 95000.0,
                "stop_loss": 94000.0,
                "take_profit": 97000.0,
            },
        )
        assert order_resp.status_code == 200
        result = order_resp.json()

        # 确认开仓成功，获取 position_id
        if "position" in result:
            position_id = result["position"]["id"]
        else:
            # pending 状态（飞书确认模式），先获取持仓
            positions_resp = api_client.get(f"/api/accounts/{account_id}/positions")
            assert positions_resp.status_code == 200
            positions = positions_resp.json()
            assert len(positions) > 0
            position_id = positions[0]["id"]

        # 更新止损止盈
        update_resp = api_client.put(
            f"/api/positions/{position_id}",
            json={"stop_loss": 94500.0, "take_profit": 97500.0},
        )
        assert update_resp.status_code == 200
        data = update_resp.json()
        assert data["stop_loss"] == 94500.0
        assert data["take_profit"] == 97500.0

    def test_close_position(self, api_client):
        """平仓"""
        # 创建账户并开仓
        create_resp = api_client.post(
            "/api/accounts",
            json={"name": "Test", "initial_balance": 10000.0, "leverage": 10},
        )
        account_id = create_resp.json()["id"]

        # 开仓
        order_resp = api_client.post(
            "/api/orders",
            json={
                "account_id": account_id,
                "symbol": "BTCUSDT",
                "side": "buy",
                "position_side": "long",
                "quantity": 0.01,
                "price": 95000.0,
            },
        )
        result = order_resp.json()

        # 获取持仓
        positions_resp = api_client.get(f"/api/accounts/{account_id}/positions")
        positions = positions_resp.json()
        if not positions:
            # 飞书确认模式，跳过开仓测试
            pytest.skip("Order requires Feishu confirmation")
        position_id = positions[0]["id"]

        # 平仓
        close_resp = api_client.delete(
            f"/api/positions/{position_id}",
            params={"exit_price": 96000.0},
        )
        assert close_resp.status_code == 200
        close_data = close_resp.json()
        assert close_data["success"] is True
        assert close_data["pnl"] is not None


class TestOrderAPI:
    """订单 API 测试"""

    def test_create_order_open_position(self, api_client):
        """开仓订单"""
        # 创建账户
        create_resp = api_client.post(
            "/api/accounts",
            json={"name": "Test", "initial_balance": 10000.0, "leverage": 10},
        )
        account_id = create_resp.json()["id"]

        # 开仓
        order_resp = api_client.post(
            "/api/orders",
            json={
                "account_id": account_id,
                "symbol": "BTCUSDT",
                "side": "buy",
                "position_side": "long",
                "quantity": 0.01,
                "price": 95000.0,
            },
        )
        assert order_resp.status_code == 200

    def test_create_order_missing_price(self, api_client):
        """开仓订单缺少价格"""
        create_resp = api_client.post(
            "/api/accounts",
            json={"name": "Test", "initial_balance": 10000.0, "leverage": 10},
        )
        account_id = create_resp.json()["id"]

        order_resp = api_client.post(
            "/api/orders",
            json={
                "account_id": account_id,
                "symbol": "BTCUSDT",
                "side": "buy",
                "position_side": "long",
                "quantity": 0.01,
            },
        )
        assert order_resp.status_code == 400

    def test_list_orders_with_filters(self, api_client):
        """订单筛选"""
        create_resp = api_client.post(
            "/api/accounts",
            json={"name": "Test", "initial_balance": 10000.0, "leverage": 10},
        )
        account_id = create_resp.json()["id"]

        # 开仓
        api_client.post(
            "/api/orders",
            json={
                "account_id": account_id,
                "symbol": "BTCUSDT",
                "side": "buy",
                "position_side": "long",
                "quantity": 0.01,
                "price": 95000.0,
            },
        )

        # 按 symbol 筛选
        response = api_client.get(
            f"/api/accounts/{account_id}/orders",
            params={"symbol": "BTCUSDT"},
        )
        assert response.status_code == 200


class TestStatsAPI:
    """统计 API 测试"""

    def test_get_account_stats(self, api_client):
        """账户统计"""
        create_resp = api_client.post(
            "/api/accounts",
            json={"name": "Test", "initial_balance": 10000.0, "leverage": 10},
        )
        account_id = create_resp.json()["id"]

        response = api_client.get(f"/api/accounts/{account_id}/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_trades" in data
        assert "win_rate" in data
        assert "current_positions" in data

    def test_get_equity_curve(self, api_client):
        """权益曲线"""
        create_resp = api_client.post(
            "/api/accounts",
            json={"name": "Test", "initial_balance": 10000.0, "leverage": 10},
        )
        account_id = create_resp.json()["id"]

        response = api_client.get(
            f"/api/accounts/{account_id}/equity-curve",
            params={"days": 30},
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_daily_stats(self, api_client):
        """每日统计"""
        create_resp = api_client.post(
            "/api/accounts",
            json={"name": "Test", "initial_balance": 10000.0, "leverage": 10},
        )
        account_id = create_resp.json()["id"]

        response = api_client.get(
            f"/api/accounts/{account_id}/stats/daily",
            params={"page": 1, "page_size": 10},
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data


class TestSignalAPI:
    """信号 API 测试"""

    def test_create_signal(self, api_client):
        """创建信号"""
        response = api_client.post(
            "/api/signals",
            json={
                "symbol": "BTCUSDT",
                "signal_type": "buy",
                "entry_price": 95000.0,
                "stop_loss": 94000.0,
                "take_profit": 97000.0,
                "timeframe": "1h",
                "reason": "Test signal",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["symbol"] == "BTCUSDT"
        assert data["status"] == "pending"

    def test_list_pending_signals(self, api_client):
        """待确认信号列表"""
        api_client.post(
            "/api/signals",
            json={"symbol": "BTCUSDT", "signal_type": "buy"},
        )

        response = api_client.get("/api/feishu/signals")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestPriceUpdateAPI:
    """价格更新 API 测试"""

    def test_update_prices(self, api_client):
        """手动更新持仓价格"""
        # 创建账户并开仓
        create_resp = api_client.post(
            "/api/accounts",
            json={"name": "Test", "initial_balance": 10000.0, "leverage": 10},
        )
        account_id = create_resp.json()["id"]

        # 开仓
        api_client.post(
            "/api/orders",
            json={
                "account_id": account_id,
                "symbol": "BTCUSDT",
                "side": "buy",
                "position_side": "long",
                "quantity": 0.01,
                "price": 95000.0,
            },
        )

        # 获取持仓
        positions_resp = api_client.get(f"/api/accounts/{account_id}/positions")
        positions = positions_resp.json()
        if not positions:
            pytest.skip("Order requires Feishu confirmation")

        # 更新价格
        price_resp = api_client.post(
            f"/api/prices/update",
            params={"account_id": account_id},
            json={"prices": {"BTCUSDT": 96000.0}},
        )
        assert price_resp.status_code == 200
        data = price_resp.json()
        assert data["updated"] == 1

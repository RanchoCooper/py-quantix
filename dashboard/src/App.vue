<template>
  <el-config-provider :locale="zhCn">
    <el-container class="app-container">
      <el-aside width="200px" class="sidebar">
        <div class="logo">
          <el-icon :size="24"><Monitor /></el-icon>
          <span>模拟交易</span>
        </div>
        <el-menu
          :default-active="$route.path"
          router
          class="sidebar-menu"
          :collapse="false"
        >
          <el-menu-item index="/">
            <el-icon><HomeFilled /></el-icon>
            <span>账户总览</span>
          </el-menu-item>
          <el-menu-item index="/trade/open">
            <el-icon><Top /></el-icon>
            <span>开仓</span>
          </el-menu-item>
          <el-menu-item index="/positions">
            <el-icon><Box /></el-icon>
            <span>持仓</span>
          </el-menu-item>
          <el-menu-item index="/trade/close">
            <el-icon><Bottom /></el-icon>
            <span>平仓</span>
          </el-menu-item>
          <el-menu-item index="/statistics">
            <el-icon><DataLine /></el-icon>
            <span>盈利统计</span>
          </el-menu-item>
          <el-menu-item index="/history">
            <el-icon><Clock /></el-icon>
            <span>历史记录</span>
          </el-menu-item>
          <el-menu-item index="/risk">
            <el-icon><Warning /></el-icon>
            <span>仓位管理</span>
          </el-menu-item>
        </el-menu>

        <!-- 账户切换 -->
        <div class="account-selector">
          <el-select
            v-model="store.currentAccountId"
            placeholder="选择账户"
            size="small"
            @change="onAccountChange"
          >
            <el-option
              v-for="acc in store.accounts"
              :key="acc.id"
              :label="acc.name"
              :value="acc.id"
            />
          </el-select>
          <el-button
            type="primary"
            size="small"
            plain
            @click="showCreateAccount = true"
          >
            新建
          </el-button>
        </div>
      </el-aside>

      <el-main class="main-content">
        <router-view />
      </el-main>
    </el-container>

    <!-- 创建账户对话框 -->
    <el-dialog v-model="showCreateAccount" title="创建模拟账户" width="400px">
      <el-form :model="newAccount" label-width="100px">
        <el-form-item label="账户名称">
          <el-input v-model="newAccount.name" placeholder="例如: 我的模拟账户" />
        </el-form-item>
        <el-form-item label="初始资金">
          <el-input-number
            v-model="newAccount.initial_balance"
            :min="100"
            :step="1000"
            :precision="2"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="杠杆倍数">
          <el-input-number
            v-model="newAccount.leverage"
            :min="1"
            :max="125"
            :step="1"
            style="width: 100%"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateAccount = false">取消</el-button>
        <el-button type="primary" @click="createAccount">创建</el-button>
      </template>
    </el-dialog>
  </el-config-provider>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import {
  HomeFilled, Top, Box, Bottom, DataLine, Clock, Warning, Monitor
} from '@element-plus/icons-vue'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import { ElMessage } from 'element-plus'
import { useAppStore } from '@/stores/app'
import { accountApi } from '@/api'

const store = useAppStore()
const showCreateAccount = ref(false)
const newAccount = ref({
  name: '',
  initial_balance: 10000,
  leverage: 10,
})

onMounted(async () => {
  await store.loadAccounts()
})

async function onAccountChange(accountId: string) {
  store.setAccount(accountId)
  await store.refresh(accountId)
}

async function createAccount() {
  if (!newAccount.value.name.trim()) {
    ElMessage.warning('请输入账户名称')
    return
  }
  try {
    const account = await accountApi.create(newAccount.value) as any
    store.accounts.unshift(account)
    store.currentAccountId = account.id
    showCreateAccount.value = false
    newAccount.value = { name: '', initial_balance: 10000, leverage: 10 }
    ElMessage.success('账户创建成功')
  } catch (e) {
    // error handled by interceptor
  }
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body, #app {
  height: 100%;
}

.app-container {
  height: 100vh;
}

.sidebar {
  background: #1a1a2e;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
}

.logo {
  padding: 20px 16px;
  display: flex;
  align-items: center;
  gap: 8px;
  color: #fff;
  font-size: 16px;
  font-weight: 600;
  border-bottom: 1px solid #2a2a4e;
}

.sidebar-menu {
  background: transparent;
  border: none;
  flex: 1;
}

.sidebar-menu .el-menu-item {
  color: #a0a0c0;
  height: 48px;
  line-height: 48px;
}

.sidebar-menu .el-menu-item:hover,
.sidebar-menu .el-menu-item.is-active {
  background: #2a2a4e;
  color: #fff;
}

.account-selector {
  padding: 12px;
  border-top: 1px solid #2a2a4e;
  display: flex;
  gap: 8px;
}

.account-selector .el-select {
  flex: 1;
}

.main-content {
  background: #f5f5f7;
  padding: 20px;
  overflow-y: auto;
}

/* 通用卡片样式 */
.page-card {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 16px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}

.page-title {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 16px;
  color: #333;
}

/* PnL 颜色 */
.pnl-positive { color: #f56c6c; }
.pnl-negative { color: #67c23a; }
</style>

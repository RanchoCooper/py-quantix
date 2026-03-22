import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Account, AccountStats, Position } from '@/api'
import { accountApi, positionApi } from '@/api'

export const useAppStore = defineStore('app', () => {
  const accounts = ref<Account[]>([])
  const currentAccountId = ref<string | null>(null)
  const positions = ref<Position[]>([])
  const stats = ref<AccountStats | null>(null)
  const loading = ref(false)

  const currentAccount = computed(() =>
    accounts.value.find((a) => a.id === currentAccountId.value)
  )

  async function loadAccounts() {
    loading.value = true
    try {
      accounts.value = await accountApi.list() as any
      if (accounts.value.length > 0 && !currentAccountId.value) {
        currentAccountId.value = accounts.value[0].id
      }
    } finally {
      loading.value = false
    }
  }

  async function loadPositions(accountId: string) {
    positions.value = await positionApi.list(accountId) as any
  }

  async function loadStats(accountId: string) {
    stats.value = await accountApi.stats(accountId) as any
  }

  async function refresh(accountId: string) {
    await Promise.all([loadPositions(accountId), loadStats(accountId)])
  }

  function setAccount(id: string) {
    currentAccountId.value = id
  }

  return {
    accounts,
    currentAccountId,
    currentAccount,
    positions,
    stats,
    loading,
    loadAccounts,
    loadPositions,
    loadStats,
    refresh,
    setAccount,
  }
})

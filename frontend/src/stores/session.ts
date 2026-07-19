import { defineStore } from 'pinia'
import { ref } from 'vue'
import { workflowApi } from '@/api/workflow'

const STORAGE_KEY = 'ari_session'

export const useSessionStore = defineStore('session', () => {
  const saved = JSON.parse(localStorage.getItem(STORAGE_KEY) || 'null')
  const sessionId = ref<string | null>(saved?.sessionId ?? null)
  const appUrl = ref(saved?.appUrl ?? '')
  const userGoal = ref(saved?.userGoal ?? '')
  const historyList = ref<any[]>([])

  function _persist() {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({
      sessionId: sessionId.value,
      appUrl: appUrl.value,
      userGoal: userGoal.value,
    }))
  }

  function setSession(id: string, url: string, goal: string) {
    sessionId.value = id
    appUrl.value = url
    userGoal.value = goal
    _persist()
  }

  function clearSession() {
    sessionId.value = null
    appUrl.value = ''
    userGoal.value = ''
    localStorage.removeItem(STORAGE_KEY)
  }

  async function loadHistory() {
    try {
      const res: any = await workflowApi.listSessions()
      historyList.value = res.data || []
    } catch {
      historyList.value = []
    }
  }

  function switchSession(id: string, url: string, goal: string) {
    setSession(id, url, goal)
  }

  return {
    sessionId, appUrl, userGoal, historyList,
    setSession, clearSession, loadHistory, switchSession,
  }
})
import api from './index'

export const monitorApi = {
  getStats(sessionId: string) {
    return api.get('/monitor/stats', { params: { session_id: sessionId } })
  },
  getCallLogs(sessionId: string) {
    return api.get('/monitor/call-logs', { params: { session_id: sessionId } })
  },
}

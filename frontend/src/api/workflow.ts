import api from './index'

export const workflowApi = {
  start(appUrl: string, userGoal?: string) {
    return api.post('/workflow/start', { app_url: appUrl, user_goal: userGoal })
  },
  getStatus(sessionId: string) {
    return api.get(`/workflow/${sessionId}/status`)
  },
  getLogs(sessionId: string) {
    return api.get(`/workflow/${sessionId}/logs`)
  },
  getSession(sessionId: string) {
    return api.get(`/workflow/${sessionId}/session`)
  },
  listSessions() {
    return api.get('/workflow/sessions')
  },
}

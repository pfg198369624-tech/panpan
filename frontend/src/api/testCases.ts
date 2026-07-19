import api from './index'

export const testCasesApi = {
  getAll(sessionId: string) {
    return api.get('/test-cases', { params: { session_id: sessionId } })
  },
}

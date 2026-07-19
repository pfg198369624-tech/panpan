import api from './index'

export const analysisApi = {
  getClassifications(sessionId: string) {
    return api.get('/analysis/classifications', { params: { session_id: sessionId } })
  },
  getFindings(sessionId: string) {
    return api.get('/analysis/findings', { params: { session_id: sessionId } })
  },
  getScope(sessionId: string) {
    return api.get('/analysis/scope', { params: { session_id: sessionId } })
  },
}

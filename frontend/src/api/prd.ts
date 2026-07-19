import api from './index'

export const prdApi = {
  getVersions(sessionId: string) {
    return api.get('/prd/versions', { params: { session_id: sessionId } })
  },
  getRequirements(sessionId: string) {
    return api.get('/prd/requirements', { params: { session_id: sessionId } })
  },
}

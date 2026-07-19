import api from './index'

export const reviewsApi = {
  getRaw(sessionId: string) {
    return api.get('/reviews/raw', { params: { session_id: sessionId } })
  },
  getCleaned(sessionId: string) {
    return api.get('/reviews/cleaned', { params: { session_id: sessionId } })
  },
}

import api from './index'

export const dataSourceApi = {
  getInfo() {
    return api.get('/data-source/info')
  },
}

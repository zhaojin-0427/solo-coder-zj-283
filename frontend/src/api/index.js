import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 10000
})

export const getImageUrl = (filename) => {
  if (!filename) return ''
  return `/uploads/${filename}`
}

export const formatDate = (date) => {
  if (!date) return ''
  const d = new Date(date)
  const year = d.getFullYear()
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

export const materialApi = {
  list: (params) => api.get('/materials', { params }),
  get: (id) => api.get(`/materials/${id}`),
  create: (data) => api.post('/materials', data, { headers: { 'Content-Type': 'multipart/form-data' } }),
  update: (id, data) => api.put(`/materials/${id}`, data, { headers: { 'Content-Type': 'multipart/form-data' } }),
  delete: (id) => api.delete(`/materials/${id}`)
}

export const projectApi = {
  list: (params) => api.get('/projects', { params }),
  get: (id) => api.get(`/projects/${id}`),
  create: (data) => api.post('/projects', data),
  update: (id, data) => api.put(`/projects/${id}`, data),
  delete: (id) => api.delete(`/projects/${id}`),
  addMaterial: (id, data) => api.post(`/projects/${id}/materials`, data),
  addPhoto: (id, data) => api.post(`/projects/${id}/photos`, data, { headers: { 'Content-Type': 'multipart/form-data' } })
}

export const materialUsageApi = {
  delete: (id) => api.delete(`/material-usages/${id}`)
}

export const processPhotoApi = {
  list: (params) => api.get('/process-photos', { params }),
  update: (id, data) => api.put(`/process-photos/${id}`, data),
  delete: (id) => api.delete(`/process-photos/${id}`)
}

export const orderApi = {
  list: (params) => api.get('/orders', { params }),
  get: (id) => api.get(`/orders/${id}`),
  create: (data) => api.post('/orders', data),
  update: (id, data) => api.put(`/orders/${id}`, data),
  delete: (id) => api.delete(`/orders/${id}`),
  getSuggestedPrice: (id) => api.get(`/orders/${id}/suggested-price`)
}

export const statisticsApi = {
  overview: () => api.get('/statistics/overview'),
  consumption: () => api.get('/statistics/material-consumption'),
  utilization: () => api.get('/statistics/utilization'),
  projectTypes: () => api.get('/statistics/project-types'),
  idleMaterials: (params) => api.get('/statistics/idle-materials', { params }),
  costTrend: () => api.get('/statistics/cost-trend'),
  anomalies: () => api.get('/statistics/anomalies'),
  orderOverview: () => api.get('/statistics/order-overview'),
  orderTrend: () => api.get('/statistics/order-trend')
}

export default api

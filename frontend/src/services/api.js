import axios from 'axios'
const api = axios.create({
  baseURL: '',
  timeout: 8000,
})
api.interceptors.request.use(cfg=>{
  const t = localStorage.getItem('token')
  if(t) cfg.headers.Authorization = `Bearer ${t}`
  return cfg
})
export default api

export const authAPI = {
  login: (u,p)=> api.post('/api/auth/login',{username:u,password:p}).then(r=>r.data)
}
export const eventAPI = {
  create: (d)=> api.post('/api/events',d).then(r=>r.data),
  get: (id)=> api.get(`/api/events/${id}`).then(r=>r.data),
  list: ()=> api.get('/api/events').then(r=>r.data),
  update: (id,d)=> api.put(`/api/events/${id}`,d).then(r=>r.data),
  qr: (id)=> `/api/events/${id}/qr`,
  qrUrl: (id)=> api.get(`/api/events/${id}/qr-url`).then(r=>r.data),
}
export const teamAPI = {
  create: (eventId,name)=> api.post(`/api/events/${eventId}/teams`,{name}).then(r=>r.data),
  list: (eventId)=> api.get(`/api/events/${eventId}/teams`).then(r=>r.data),
  update: (teamId,name)=> api.put(`/api/teams/${teamId}`,{name}).then(r=>r.data),
  del: (teamId)=> api.delete(`/api/teams/${teamId}`).then(r=>r.data),
}
export const questionAPI = {
  create: (eventId,q)=> api.post(`/api/events/${eventId}/questions`,q).then(r=>r.data),
  list: (eventId)=> api.get(`/api/events/${eventId}/questions`).then(r=>r.data),
  update: (qid,q)=> api.put(`/api/questions/${qid}`,q).then(r=>r.data),
  del: (qid)=> api.delete(`/api/questions/${qid}`).then(r=>r.data),
  reorder: (eventId,order)=> api.post(`/api/events/${eventId}/questions/reorder`,{order}).then(r=>r.data),
}
export const participantAPI = {
  join: (code,payload)=> api.post(`/api/events/${code}/join`,payload).then(r=>r.data),
  list: (eventId)=> api.get(`/api/events/${eventId}/participants`).then(r=>r.data),
}
export const roundAPI = {
  start: (eventId)=> api.post(`/api/events/${eventId}/round/start`).then(r=>r.data),
  open: (eventId)=> api.post(`/api/events/${eventId}/round/open-buzzer`).then(r=>r.data),
  reset: (eventId)=> api.post(`/api/events/${eventId}/round/reset`).then(r=>r.data),
  next: (eventId)=> api.post(`/api/events/${eventId}/round/next`).then(r=>r.data),
  prev: (eventId)=> api.post(`/api/events/${eventId}/round/prev`).then(r=>r.data),
  state: (eventId)=> api.get(`/api/events/${eventId}/round/state`).then(r=>r.data),
}

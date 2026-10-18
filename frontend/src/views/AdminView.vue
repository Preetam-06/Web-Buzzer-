<template>
  <div class="admin-page" style="min-height:100vh">
    <!-- Topbar -->
    <div class="topbar">
      <div class="container" style="display:flex;justify-content:space-between;align-items:center;padding:14px 0;gap:12px;flex-wrap:wrap">
        <div style="display:flex;align-items:center;gap:10px">
          <span style="width:38px;height:38px;border-radius:12px;background:linear-gradient(145deg,#62e9ff,#0a8fb0);color:#04293a;display:grid;place-items:center;font-weight:900;box-shadow:0 0 14px rgba(0,239,255,.6)">⚡</span>
          <div>
            <div style="font-weight:900;letter-spacing:-.02em">Faculty Trivia Buzzer — Admin</div>
            <div style="font-size:12px;color:var(--muted)">Desktop control • Responsive for tablet too</div>
          </div>
        </div>
        <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap">
          <input v-model="loginUser" placeholder="admin" class="input" style="width:120px" v-if="!isAuthed" />
          <input v-model="loginPass" type="password" placeholder="password" class="input" style="width:140px" v-if="!isAuthed" />
          <button v-if="!isAuthed" class="btn btn-primary" @click="doLogin">Login</button>
          <button v-else class="btn btn-ghost" @click="logout">Logout ({{ authUser }})</button>
        </div>
      </div>
    </div>

    <div v-if="!isAuthed" class="container" style="padding:40px 0;text-align:center;color:var(--muted)">Login as admin to manage event. Default: admin / admin123</div>

    <template v-else>
      <div class="container" style="padding:20px 0 28px;display:grid;gap:18px">
        <!-- Event selector / creator -->
        <div class="grid grid-2">
          <div class="card">
            <div style="font-weight:800;margin-bottom:12px">Event</div>
            <div v-if="!selectedEvent" style="display:grid;gap:10px">
              <div class="grid grid-2">
                <div><label class="label">Event Name</label><input v-model="newEvent.name" class="input" placeholder="Faculty Trivia 2026"/></div>
                <div><label class="label">Code (3-20, A-Z0-9_-)</label><input v-model="newEvent.code" class="input" placeholder="FACULTY26"/></div>
              </div>
              <div class="grid grid-2">
                <div><label class="label">Max Participants</label><input v-model.number="newEvent.max" type="number" min="1" class="input" /></div>
                <div><label class="label">Users per team</label><input v-model.number="newEvent.teamLimit" type="number" min="1" class="input" placeholder="Unlimited" /></div>
              </div>
              <button class="btn btn-primary" @click="createEvent">Create Event</button>
              <div style="font-size:13px;color:var(--muted)">Or select existing:</div>
              <div style="display:flex;gap:8px;flex-wrap:wrap">
                <button v-for="e in events" :key="e.id" class="btn btn-ghost" @click="selectEvent(e)">{{ e.name }} ({{ e.code }})</button>
              </div>
            </div>
            <div v-else>
              <div style="display:flex;justify-content:space-between;align-items:start;gap:10px;flex-wrap:wrap">
                <div>
                  <div style="font-weight:800;font-size:18px">{{ selectedEvent.name }} <span class="badge badge-muted">{{ selectedEvent.code }}</span></div>
                  <div style="font-size:13px;color:var(--muted)">{{ participantCount }} / {{ selectedEvent.max_participants }} participants • Status: {{ selectedEvent.status }}</div>
                </div>
                <button class="btn btn-ghost" @click="selectedEvent=null; loadEvents()">Change</button>
              </div>
              <div style="margin-top:12px;display:flex;gap:8px;flex-wrap:wrap">
                <label class="label" style="align-self:center;margin:0">Max</label>
                <input v-model.number="editMax" type="number" class="input" style="width:110px"/>
                <label class="label" style="align-self:center;margin:0">Users/team</label>
                <input v-model.number="editTeamLimit" type="number" min="1" class="input" style="width:110px" placeholder="Unlimited"/>
                <button class="btn btn-ghost" @click="updateLimits">Save limits</button>
                <a :href="displayUrl" target="_blank" class="btn btn-ghost">Open Display ↗</a>
                <a :href="joinUrl" target="_blank" class="btn btn-ghost">Join Link ↗</a>
              </div>
              <div v-if="networkInfo.lan_ip && networkInfo.lan_ip!=='localhost'" style="margin-top:8px;background:linear-gradient(145deg,rgba(255,255,255,.7),rgba(169,219,227,.5));border:1px solid rgba(255,255,255,.7);border-radius:14px;padding:8px 10px;font-size:12px">
                <div style="font-weight:700;color:#0a6d8a">✓ Phones use: {{ joinUrl }}</div>
                <div style="color:#3d6f80">LAN IP: {{ networkInfo.lan_ip }}:{{ networkInfo.port }} — QR auto uses IP, not localhost</div>
              </div>
              <div v-else-if="networkInfo.lan_ip==='localhost'" style="margin-top:8px;background:linear-gradient(145deg,#ffe6a8,#ffc46b);border:1px solid rgba(255,255,255,.7);border-radius:14px;padding:8px 10px;font-size:12px;color:#4a2d00">⚠️ LAN IP not detected — QR shows localhost. Phones can't join localhost. Connect to Wi-Fi and restart backend.</div>
              <div style="margin-top:12px">
                <QRCode :code="selectedEvent.code" :eventId="selectedEvent.id" />
              </div>
            </div>
          </div>

          <div class="card">
            <div style="font-weight:800;margin-bottom:12px">Round Control</div>
            <div v-if="!selectedEvent" style="color:var(--muted)">Select event first</div>
            <div v-else style="display:grid;gap:10px">
              <div style="display:flex;gap:8px;flex-wrap:wrap">
                <span class="badge" :class="buzzerBadge">{{ roundState.buzzer_status || 'WAITING' }}</span>
                <span v-if="roundState.question" class="badge badge-muted">Q{{ roundState.question.number }}</span>
                <span v-if="totalQuestions" class="badge badge-muted">Q {{ questionIndex }} / {{ totalQuestions }}</span>
                <span v-if="queOver" class="badge badge-warning">QUE OVER</span>
                <span v-if="roundState.winner" class="badge badge-success">Winner: {{ roundState.winner.participant_name }} ({{ roundState.winner.team_name }})</span>
              </div>
              <div v-if="queOver" style="background:linear-gradient(145deg,#ffe6a8,#ffc46b);border:1px solid rgba(255,255,255,.7);padding:10px 12px;font-weight:800;color:#4a2d00">QUE OVER — all questions done. Use PREV to go back.</div>
              <div v-if="roundState.question && !queOver" style="background:linear-gradient(145deg,#8abdc9,#c6edf3);border:1px solid rgba(255,255,255,.6);border-radius:16px;padding:12px;box-shadow:inset 5px 5px 12px rgba(11,53,71,.2), inset -5px -5px 12px rgba(255,255,255,.7)">
                <div style="font-weight:700">{{ roundState.question.text }}</div>
                <div v-if="roundState.question.options" style="margin-top:6px;display:flex;gap:6px;flex-wrap:wrap">
                  <span v-for="(o,i) in roundState.question.options" :key="i" class="badge badge-muted">{{ String.fromCharCode(65+i) }}: {{ o }}</span>
                </div>
              </div>
              <div v-else-if="!queOver" style="color:var(--muted);font-size:14px">No active question — click Start Question</div>
              <div style="display:grid;grid-template-columns:repeat(2,1fr);gap:10px">
                <button class="btn btn-primary" @click="startQ">START QUESTION</button>
                <button class="btn btn-primary" :disabled="roundState.buzzer_status==='BUZZER_OPEN' || queOver" @click="openBuzzer" style="background:linear-gradient(145deg,#5ff0d6,#00bfa0)">OPEN BUZZER</button>
                <button class="btn btn-ghost" @click="resetBuzzer">RESET BUZZER</button>
                <button class="btn btn-ghost" :disabled="isFirst && !queOver" @click="prevQ">← PREV QUESTION</button>
              </div>
              <div style="display:grid;grid-template-columns:1fr;gap:10px">
                <button class="btn btn-ghost" :disabled="queOver" @click="nextQ">NEXT QUESTION →</button>
              </div>
              <div style="font-size:12px;color:var(--muted)">Flow: Start Question → Open Buzzer → Reset → Prev / Next</div>
            </div>
          </div>
        </div>

        <div class="grid grid-3" v-if="selectedEvent">
          <!-- Teams -->
          <div class="card">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px">
              <div style="font-weight:800">Teams</div>
              <span class="badge badge-muted">{{ teams.length }}</span>
            </div>
            <form @submit.prevent="addTeam" style="display:flex;gap:8px;margin-bottom:12px">
              <button class="btn btn-primary" type="submit" :disabled="teams.length >= 24">Add next team</button>
              <span style="font-size:12px;color:var(--muted);align-self:center">Fixed names: TEAM_01 to TEAM_24</span>
            </form>
            <div style="display:grid;gap:8px;max-height:340px;overflow:auto">
              <div v-for="t in teams" :key="t.id" style="display:flex;justify-content:space-between;align-items:center;border:1px solid rgba(255,255,255,.65);padding:10px 12px;background:linear-gradient(145deg,rgba(255,255,255,.6),rgba(147,203,214,.4));box-shadow:4px 4px 10px rgba(11,53,71,.15), -4px -4px 10px rgba(255,255,255,.6);gap:8px;flex-wrap:wrap">
                <div>
                  <div style="font-weight:700">{{ t.name }}</div>
                  <div style="font-size:12px;color:var(--muted)">{{ t.member_count }} members</div>
                </div>
                <div style="display:flex;gap:6px;flex-wrap:wrap">
                  <button class="btn btn-ghost" style="padding:6px 10px;font-size:12px;color:var(--danger)" @click="deleteTeam(t)">Delete</button>
                </div>
              </div>
              <div v-if="teams.length===0" style="color:var(--muted);text-align:center;padding:16px">No teams yet</div>
            </div>
          </div>

          <!-- Participants -->
          <div class="card">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px">
              <div style="font-weight:800">Participants</div>
              <span class="badge badge-success">{{ participants.length }}</span>
            </div>
            <div style="display:grid;gap:8px;max-height:420px;overflow:auto">
              <div v-for="p in participants" :key="p.id" style="display:flex;justify-content:space-between;align-items:center;border:1px solid rgba(255,255,255,.65);border-radius:16px;padding:10px 12px;background:linear-gradient(145deg,rgba(255,255,255,.55),rgba(147,203,214,.35))">
                <div><div style="font-weight:600">{{ p.name }}</div><div style="font-size:12px;color:var(--muted)">{{ p.team_name }} • {{ p.id.slice(0,6) }}</div></div>
                <span class="badge badge-muted">{{ p.team_name }}</span>
              </div>
              <div v-if="participants.length===0" style="color:var(--muted);text-align:center;padding:16px">No participants yet — share QR</div>
            </div>
          </div>

          <!-- Questions -->
          <div class="card">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px">
              <div style="font-weight:800">Questions</div>
              <span class="badge badge-muted">{{ questions.length }}</span>
            </div>
            <form @submit.prevent="addQuestion" style="display:grid;gap:8px;margin-bottom:12px">
              <textarea v-model="newQ.text" class="input" placeholder="Question text" rows="2" required></textarea>
              <input v-model="newQ.optionsRaw" class="input" placeholder="Options comma separated (optional) — e.g. Earth,Mars,Jupiter"/>
              <button class="btn btn-primary" type="submit">Add Question</button>
            </form>
            <div style="display:grid;gap:8px;max-height:360px;overflow:auto">
              <div v-for="q in questions" :key="q.id" style="border:1px solid rgba(255,255,255,.65);border-radius:16px;padding:10px 12px;background:linear-gradient(145deg,rgba(255,255,255,.6),rgba(147,203,214,.4))">
                <div style="display:flex;justify-content:space-between;gap:8px">
                  <b>Q{{ q.number }}</b>
                  <span style="display:flex;gap:6px">
                    <button class="btn btn-ghost" style="padding:4px 8px;font-size:12px" @click="editQuestion(q)">Edit</button>
                    <button class="btn btn-ghost" style="padding:4px 8px;font-size:12px;color:var(--danger)" @click="removeQuestion(q)">Del</button>
                  </span>
                </div>
                <div style="font-size:14px;margin-top:4px">{{ q.text }}</div>
                <div v-if="q.options" style="margin-top:6px;display:flex;gap:6px;flex-wrap:wrap"><span v-for="(o,i) in q.options" :key="i" class="badge badge-muted">{{ o }}</span></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
<script setup>
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import { authAPI, eventAPI, teamAPI, questionAPI, participantAPI, roundAPI } from '../services/api'
import api from '../services/api'
import QRCode from '../components/QRCode.vue'

const isAuthed = ref(!!localStorage.getItem('token'))
const authUser = ref(localStorage.getItem('user')||'admin')
const loginUser = ref('admin')
const loginPass = ref('admin123')

async function doLogin(){
  try{
    const r = await authAPI.login(loginUser.value, loginPass.value)
    localStorage.setItem('token', r.access_token)
    localStorage.setItem('user', loginUser.value)
    isAuthed.value=true
    authUser.value=loginUser.value
    loadEvents()
  }catch(e){ alert(e.response?.data?.detail || 'Login failed') }
}
function logout(){
  localStorage.removeItem('token')
  isAuthed.value=false
}

const events = ref([])
const selectedEvent = ref(null)
const newEvent = ref({ name:'', code:'', max:50, teamLimit:2 })
const editMax = ref(50)
const editTeamLimit = ref(null)
const teams = ref([])
const participants = ref([])
const questions = ref([])
const roundState = ref({ buzzer_status:'WAITING' })
const newQ = ref({ text:'', optionsRaw:'' })
const queOver = computed(()=> !!roundState.value.que_over)
const totalQuestions = computed(()=> Number(roundState.value.total_questions||0))
const questionIndex = computed(()=> Number(roundState.value.question_index||0))
const isFirst = computed(()=> roundState.value.is_first !== false && questionIndex.value <= 1)
const participantCount = computed(()=> participants.value.length)

const buzzerBadge = computed(()=>{
  const s = roundState.value.buzzer_status
  if(s==='BUZZER_OPEN') return 'badge-success'
  if(s==='BUZZER_LOCKED') return 'badge-danger'
  return 'badge-muted'
})

const networkInfo = ref({ lan_ip:'', port:'8000' })
const joinUrl = ref('')
const displayUrl = ref('')
let refreshTimer = null
let refreshInProgress = false
async function fetchNetwork(){
  try{
    const { data } = await api.get('/api/network-info')
    networkInfo.value = data
    if(selectedEvent.value){
      const port = location.port ? `:${location.port}` : ''
      const origin = data.lan_ip && data.lan_ip !== 'localhost'
        ? `${location.protocol}//${data.lan_ip}${port}`
        : location.origin
      joinUrl.value = `${origin}/join/${selectedEvent.value.code}`
      displayUrl.value = `${origin}/display/${selectedEvent.value.code}`
    }
  }catch{
    // fallback to location
    if(selectedEvent.value){
      joinUrl.value = `${location.origin}/join/${selectedEvent.value.code}`
      displayUrl.value = `${location.origin}/display/${selectedEvent.value.code}`
    }
  }
}

async function loadEvents(){
  try{ events.value = await eventAPI.list() }catch{}
}
async function createEvent(){
  if(!newEvent.value.name || !newEvent.value.code){ alert('Fill name & code'); return }
  try{
    const teamLimit = Number(newEvent.value.teamLimit)
    const ev = await eventAPI.create({
      name:newEvent.value.name,
      code:newEvent.value.code.toUpperCase(),
      max_participants: Number(newEvent.value.max)||50,
      team_member_limit: teamLimit > 0 ? teamLimit : null
    })
    selectedEvent.value = ev
    editMax.value = ev.max_participants
    editTeamLimit.value = ev.team_member_limit
    await refreshAll()
    await fetchNetwork()
    loadEvents()
  }catch(e){ alert(e.response?.data?.detail || e.message) }
}
async function selectEvent(ev){
  selectedEvent.value = ev
  editMax.value = ev.max_participants
  editTeamLimit.value = ev.team_member_limit
  await refreshAll()
  await fetchNetwork()
}
async function updateLimits(){
  try{
    const teamLimit = Number(editTeamLimit.value)
    const ev = await eventAPI.update(selectedEvent.value.id, {
      max_participants: Number(editMax.value),
      team_member_limit: teamLimit > 0 ? teamLimit : null
    })
    selectedEvent.value = ev
  }catch(e){ alert(e.response?.data?.detail || e.message) }
}
async function refreshAll(){
  if(!selectedEvent.value || refreshInProgress) return
  refreshInProgress=true
  try{
    const id = selectedEvent.value.id
    try{ teams.value = await teamAPI.list(id) }catch{}
    try{ participants.value = await participantAPI.list(id) }catch{}
    try{ questions.value = await questionAPI.list(id) }catch{}
    try{ roundState.value = await roundAPI.state(id) }catch{}
    try{ selectedEvent.value = await eventAPI.get(id) }catch{}
  }finally{ refreshInProgress=false }
}

async function addTeam(){
  try{
    await teamAPI.create(selectedEvent.value.id, '')
    refreshAll()
  }catch(e){ alert(e.response?.data?.detail || e.message) }
}
async function deleteTeam(t){
  if(!confirm(`Delete ${t.name}?`)) return
  try{ await teamAPI.del(t.id); refreshAll() }catch(e){ alert(e.response?.data?.detail || e.message) }
}
async function addQuestion(){
  const opts = newQ.value.optionsRaw ? newQ.value.optionsRaw.split(',').map(s=>s.trim()).filter(Boolean) : undefined
  await questionAPI.create(selectedEvent.value.id, { text:newQ.value.text, options: opts })
  newQ.value = { text:'', optionsRaw:'' }
  refreshAll()
}
async function editQuestion(q){
  const txt = prompt('Edit question', q.text)
  if(txt===null) return
  await questionAPI.update(q.id, { text: txt })
  refreshAll()
}
async function removeQuestion(q){
  if(!confirm('Delete question?')) return
  await questionAPI.del(q.id)
  refreshAll()
}
async function startQ(){ try{ await roundAPI.start(selectedEvent.value.id) }catch(e){ if(e.response?.data?.detail!=='No more questions') alert(e.response?.data?.detail || e.message) } refreshAll() }
async function openBuzzer(){ try{ await roundAPI.open(selectedEvent.value.id) }catch(e){ alert(e.response?.data?.detail || e.message) } refreshAll() }
async function resetBuzzer(){ await roundAPI.reset(selectedEvent.value.id); refreshAll() }
async function nextQ(){ try{ await roundAPI.next(selectedEvent.value.id) }catch(e){ if(e.response?.data?.detail!=='No more questions') alert(e.response?.data?.detail || e.message) } refreshAll() }
async function prevQ(){ try{ await roundAPI.prev(selectedEvent.value.id); refreshAll() }catch(e){ alert(e.response?.data?.detail || e.message) } }

onMounted(()=>{ if(isAuthed.value) loadEvents(); fetchNetwork() })
watch(selectedEvent, (v)=>{
  if(refreshTimer) clearInterval(refreshTimer)
  refreshTimer = null
  if(v){
    refreshTimer = setInterval(refreshAll, 3000)
  }
})
onBeforeUnmount(()=>{ if(refreshTimer) clearInterval(refreshTimer) })
</script>

<template>
  <div class="display-page" style="min-height:100vh;background:#020617;padding:12px;display:flex;flex-direction:column;gap:12px">
    <div style="display:flex;justify-content:space-between;align-items:center;color:#cbd5e1;padding:6px 6px">
      <div style="display:flex;gap:10px;align-items:center">
        <span style="background:var(--primary);color:#fff;padding:6px 10px;border-radius:10px;font-weight:900">TRIVIA</span>
        <span style="font-weight:700;color:#f1f5f9">{{ event?.name || code }}</span>
        <span class="badge" style="background:#1e293b;color:#cbd5e1">{{ status }}</span>
      </div>
      <div style="display:flex;gap:8px;align-items:center">
        <button class="btn btn-ghost" style="padding:8px 12px;background:#1e293b;color:#fff;border-color:#334155" @click="toggleFs">⛶ Fullscreen</button>
        <span style="font-size:12px">{{ participants.length }} players • {{ teams.length }} teams</span>
      </div>
    </div>

    <div ref="frameRef" class="display-frame" style="flex:1;min-height:0">
      <!-- Slide content -->
      <div style="flex:1;display:flex;flex-direction:column;padding:clamp(18px,3vw,40px);justify-content:center;min-height:0">
        <template v-if="!question && status==='WAITING'">
          <div style="text-align:center">
            <div style="font-size:clamp(24px,4vw,52px);font-weight:900;letter-spacing:-.02em">Welcome to {{ event?.name || 'Trivia Night' }}</div>
            <div style="margin-top:12px;color:#94a3b8;font-size:clamp(14px,1.8vw,20px)">Scan QR on your phone to join • Code: <b style="color:#fff">{{ code }}</b></div>
            <div style="margin-top:18px;display:grid;place-items:center">
              <img v-if="qrSrc" :src="qrSrc" alt="QR" style="width:min(260px,40vw);height:auto;background:#080909;padding:10px;border-radius:16px"/>
            </div>
          </div>
        </template>

        <template v-else-if="winner">
          <div style="text-align:center">
            <div style="font-size:14px;letter-spacing:.18em;color:#facc15;font-weight:800">FIRST BUZZER</div>
            <div class="display-winner" style="margin-top:8px;color:#fff">{{ winner.participant_name }}</div>
            <div style="margin-top:8px;font-size:clamp(18px,2.8vw,34px);font-weight:700;color:#c084fc">{{ winner.team_name }}</div>
            <div style="margin-top:16px;color:#94a3b8">Team to answer verbally — host to judge</div>
          </div>
        </template>

        <template v-else-if="question">
          <div style="display:flex;flex-direction:column;gap:18px">
            <div style="display:flex;gap:10px;align-items:center">
              <span style="background:#facc15;color:#0f172a;font-weight:900;padding:6px 12px;border-radius:999px;font-size:12px">Q{{ question.number }}</span>
              <span :class="['badge', buzzerStatus==='BUZZER_OPEN'?'badge-success':'badge-muted']" style="font-size:12px">{{ buzzerStatus==='BUZZER_OPEN'?'BUZZER OPEN':'GET READY'}}</span>
            </div>
            <div class="display-q">{{ question.text }}</div>
            <div v-if="question.options && question.options.length" style="display:grid;gap:10px;grid-template-columns:repeat(2,1fr);margin-top:6px">
              <div v-for="(opt,i) in question.options" :key="i" style="background:#080909;border:1px solid rgba(242,238,230,.25);border-radius:14px;padding:14px 16px;font-weight:700">{{ String.fromCharCode(65+i) }}. {{ opt }}</div>
            </div>
            <div v-if="question.image" style="margin-top:10px"><img :src="question.image" alt="q-img" style="max-height:32vh;width:auto;max-width:100%;border-radius:12px"/></div>
            <div v-if="buzzerStatus==='BUZZER_OPEN'" style="margin-top:8px;display:flex;gap:10px;align-items:center;color:#4ade80;font-weight:800"><span style="width:12px;height:12px;border-radius:50%;background:#4ade80;box-shadow:0 0 12px #4ade80;display:inline-block" class="pulse"></span> Waiting for buzzer…</div>
          </div>
        </template>
      </div>

      <!-- Bottom bar: scores -->
      <div style="background:rgba(255,255,255,.06);backdrop-filter:blur(8px);border-top:1px solid rgba(255,255,255,.1);padding:12px 16px;display:flex;gap:10px;flex-wrap:wrap;align-items:center;justify-content:space-between">
        <div style="display:flex;gap:8px;flex-wrap:wrap">
          <div v-for="t in sortedTeams" :key="t.id" style="background:#080909;border:1px solid rgba(242,238,230,.25);border-radius:999px;padding:6px 12px;display:flex;gap:8px;align-items:center;font-weight:700;font-size:13px">
            <span style="color:#f2eee6">{{ t.name }}</span><span style="background:#c9f45a;color:#080909;padding:2px 8px;border-radius:999px;font-weight:900">{{ t.score }}</span>
          </div>
        </div>
        <div style="font-size:12px;color:#94a3b8">Leaderboard • Live scores</div>
      </div>
    </div>
  </div>
</template>
<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { eventAPI, teamAPI, roundAPI } from '../services/api'
import api from '../services/api'
import { connectEventWS } from '../services/websocket'

const props = defineProps({ code:String })
const code = props.code
const event = ref(null)
const eventId = ref(null)
const qrSrc = ref('')
const question = ref(null)
const winner = ref(null)
const buzzerStatus = ref('WAITING')
const teams = ref([])
const participants = ref([])
const status = computed(()=> buzzerStatus.value)
const sortedTeams = computed(()=> [...teams.value].sort((a,b)=> b.score-a.score))
const frameRef = ref(null)

function toggleFs(){
  if(document.fullscreenElement) document.exitFullscreen()
  else frameRef.value?.requestFullscreen?.()
}

let ws=null
let teamTimer = null
async function load(){
  try{
    const ev = await eventAPI.get(code)
    event.value = ev
    eventId.value = ev.id
    try {
      const { data } = await api.get('/api/network-info')
      const port = location.port ? `:${location.port}` : ''
      const origin = data.lan_ip && data.lan_ip !== 'localhost'
        ? `${location.protocol}//${data.lan_ip}${port}`
        : location.origin
      qrSrc.value = `/api/events/${ev.id}/qr?base_url=${encodeURIComponent(origin)}`
    } catch {}
    const t = await teamAPI.list(ev.id)
    teams.value = t
    const st = await roundAPI.state(ev.id)
    if(st.question) question.value = st.question
    if(st.winner) winner.value = st.winner
    buzzerStatus.value = st.buzzer_status || 'WAITING'
  }catch{}
}
function handle(msg){
  switch(msg.type){
    case 'INIT_STATE':
      if(msg.status) buzzerStatus.value = msg.status
      if(msg.winner) winner.value = msg.winner
      if(msg.question) question.value = msg.question
      if(msg.event) { event.value = msg.event; eventId.value = msg.event.id }
      break
    case 'QUESTION_STARTED':
      question.value = msg.question
      winner.value=null
      buzzerStatus.value='QUESTION_ACTIVE'
      break
    case 'BUZZER_OPEN':
      buzzerStatus.value='BUZZER_OPEN'
      winner.value=null
      break
    case 'BUZZER_WINNER':
      winner.value = msg.winner
      buzzerStatus.value='BUZZER_LOCKED'
      break
    case 'BUZZER_CLOSED':
      if(!winner.value) buzzerStatus.value='BUZZER_LOCKED'
      break
    case 'ROUND_RESET':
      winner.value=null
      buzzerStatus.value='WAITING'
      break
    case 'SCORE_UPDATED':
      if(msg.teams) teams.value = msg.teams
      else if(eventId.value) teamAPI.list(eventId.value).then(t=> teams.value=t)
      break
    case 'ANSWER_RESULT':
      // The host confirmed the answer: remove the winner overlay and keep
      // the question visible until the next question/reset.
      winner.value=null
      buzzerStatus.value='QUESTION_ACTIVE'
      break
  }
}
onMounted(async ()=>{
  await load()
  ws = connectEventWS(code, { onMessage: handle })
  teamTimer = setInterval(async()=>{
    if(eventId.value){
      try{ teams.value = await teamAPI.list(eventId.value) }catch{}
    }
  }, 3000)
})
onBeforeUnmount(()=>{
  if(teamTimer) clearInterval(teamTimer)
  if(ws) ws.close()
})
</script>

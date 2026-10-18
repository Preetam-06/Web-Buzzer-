<template>
  <div class="display-page" style="min-height:100vh;padding:12px;display:flex;flex-direction:column;gap:12px">
    <div style="display:flex;justify-content:space-between;align-items:center;color:#0b3d51;padding:6px 6px">
      <div style="display:flex;gap:10px;align-items:center">
        <span style="background:linear-gradient(145deg,#62e9ff,#0a8fb0);color:#04293a;padding:6px 12px;border-radius:999px;font-weight:900;box-shadow:0 0 14px rgba(0,239,255,.6)">TRIVIA</span>
        <span style="font-weight:800;color:#083344">{{ event?.name || code }}</span>
        <span class="badge badge-muted">{{ status }}</span>
        <span v-if="queOver" class="badge badge-warning">QUE OVER</span>
        <span v-else-if="totalQuestions" class="badge badge-muted">Q {{ questionIndex }} / {{ totalQuestions }}</span>
      </div>
      <div style="display:flex;gap:8px;align-items:center">
        <button class="btn btn-ghost" style="padding:8px 14px" @click="toggleFs">⛶ Fullscreen</button>
        <span style="font-size:12px;color:#2f5a68;font-weight:700">{{ participants.length }} players • {{ teams.length }} teams</span>
      </div>
    </div>

    <div ref="frameRef" class="display-frame" style="flex:1;min-height:0">
      <!-- Slide content -->
      <div style="flex:1;display:flex;flex-direction:column;padding:clamp(18px,3vw,40px);justify-content:center;min-height:0">
        <template v-if="queOver">
          <div style="text-align:center">
            <div style="font-size:14px;letter-spacing:.18em;color:#0a6d8a;font-weight:800">ALL QUESTIONS DONE</div>
            <div class="display-winner" style="margin-top:8px">QUE OVER</div>
            <div style="margin-top:12px;color:#2f5a68;font-size:clamp(14px,1.8vw,20px)">Thanks for playing {{ event?.name || 'Trivia' }}</div>
          </div>
        </template>

        <template v-else-if="!question && status==='WAITING'">
          <div style="text-align:center">
            <div style="font-size:clamp(24px,4vw,52px);font-weight:900;letter-spacing:-.02em;color:#083344">Welcome to {{ event?.name || 'Trivia Night' }}</div>
            <div style="margin-top:12px;color:#2f5a68;font-size:clamp(14px,1.8vw,20px)">Scan QR on your phone to join • Code: <b style="color:#0a6d8a">{{ code }}</b></div>
            <div style="margin-top:18px;display:grid;place-items:center">
              <img v-if="qrSrc" :src="qrSrc" alt="QR" style="width:min(260px,40vw);height:auto;background:#fff;padding:12px;border-radius:22px;border:1px solid rgba(255,255,255,.8);box-shadow:8px 8px 20px rgba(11,53,71,.25), -8px -8px 20px rgba(255,255,255,.7), 0 0 22px rgba(0,239,255,.45)"/>
            </div>
          </div>
        </template>

        <template v-else-if="winner">
          <div style="text-align:center">
            <div style="font-size:14px;letter-spacing:.18em;color:#0a6d8a;font-weight:800">FIRST BUZZER</div>
            <div class="display-winner" style="margin-top:8px">{{ winner.participant_name }}</div>
            <div style="margin-top:8px;font-size:clamp(18px,2.8vw,34px);font-weight:800;color:#0b6e8a">{{ winner.team_name }}</div>
            <div style="margin-top:16px;color:#3d6f80">Team to answer verbally — host to continue</div>
          </div>
        </template>

        <template v-else-if="question">
          <div style="display:flex;flex-direction:column;gap:18px">
            <div style="display:flex;gap:10px;align-items:center">
              <span style="background:linear-gradient(145deg,#62e9ff,#0a8fb0);color:#04293a;font-weight:900;padding:6px 14px;border-radius:999px;font-size:12px;box-shadow:0 0 14px rgba(0,239,255,.55)">Q{{ question.number }}</span>
              <span :class="['badge', buzzerStatus==='BUZZER_OPEN'?'badge-success':'badge-muted']" style="font-size:12px">{{ buzzerStatus==='BUZZER_OPEN'?'BUZZER OPEN':'GET READY'}}</span>
            </div>
            <div class="display-q">{{ question.text }}</div>
            <div v-if="question.options && question.options.length" style="display:grid;gap:10px;grid-template-columns:repeat(2,1fr);margin-top:6px">
              <div v-for="(opt,i) in question.options" :key="i" style="background:linear-gradient(145deg,rgba(255,255,255,.7),rgba(147,203,214,.45));border:1px solid rgba(255,255,255,.7);border-radius:18px;padding:14px 16px;font-weight:700;color:#083344;box-shadow:5px 5px 14px rgba(11,53,71,.18), -5px -5px 14px rgba(255,255,255,.6)">{{ String.fromCharCode(65+i) }}. {{ opt }}</div>
            </div>
            <div v-if="question.image" style="margin-top:10px"><img :src="question.image" alt="q-img" style="max-height:32vh;width:auto;max-width:100%;border-radius:18px"/></div>
            <div v-if="buzzerStatus==='BUZZER_OPEN'" style="margin-top:8px;display:flex;gap:10px;align-items:center;color:#0a6d8a;font-weight:800"><span style="width:12px;height:12px;border-radius:50%;background:#00d9f5;box-shadow:0 0 14px #00efff;display:inline-block" class="pulse"></span> Waiting for buzzer…</div>
          </div>
        </template>
      </div>

      <!-- Bottom bar: progress only, no scores -->
      <div style="background:rgba(255,255,255,.4);backdrop-filter:blur(10px);border-top:1px solid rgba(255,255,255,.7);padding:12px 16px;display:flex;gap:10px;flex-wrap:wrap;align-items:center;justify-content:space-between;border-radius:0 0 26px 26px">
        <div style="display:flex;gap:8px;flex-wrap:wrap">
          <div v-for="t in teams" :key="t.id" style="background:linear-gradient(145deg,rgba(255,255,255,.75),rgba(147,203,214,.5));border:1px solid rgba(255,255,255,.7);border-radius:999px;padding:6px 12px;font-weight:700;font-size:13px;color:#083344;box-shadow:3px 3px 8px rgba(11,53,71,.18)">{{ t.name }}</div>
        </div>
        <div style="font-size:12px;color:#2f5a68;font-weight:700">{{ queOver ? 'Que over' : (totalQuestions ? `Question ${questionIndex} of ${totalQuestions}` : 'Live') }}</div>
      </div>
    </div>
  </div>
</template>
<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { eventAPI, teamAPI, participantAPI, roundAPI } from '../services/api'
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
const queOver = ref(false)
const totalQuestions = ref(0)
const questionIndex = ref(0)
const teams = ref([])
const participants = ref([])
const status = computed(()=> queOver.value ? 'QUE OVER' : buzzerStatus.value)
const frameRef = ref(null)

function toggleFs(){
  if(document.fullscreenElement) document.exitFullscreen()
  else frameRef.value?.requestFullscreen?.()
}

function applyState(st){
  if(!st) return
  if(st.question !== undefined) question.value = st.question
  if(st.winner !== undefined) winner.value = st.winner
  if(st.buzzer_status) buzzerStatus.value = st.buzzer_status
  if(st.que_over !== undefined) queOver.value = !!st.que_over
  if(st.total_questions !== undefined) totalQuestions.value = Number(st.total_questions||0)
  if(st.question_index !== undefined) questionIndex.value = Number(st.question_index||0)
}

let ws=null
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
    try{ teams.value = await teamAPI.list(ev.id) }catch{}
    try{ participants.value = await participantAPI.list(ev.id) }catch{}
    const st = await roundAPI.state(ev.id)
    applyState(st)
  }catch{}
}
function handle(msg){
  switch(msg.type){
    case 'INIT_STATE':
      if(msg.status) buzzerStatus.value = msg.status
      if(msg.winner) winner.value = msg.winner
      if(msg.question) question.value = msg.question
      if(msg.event) {
        event.value = msg.event
        eventId.value = msg.event.id
        if(msg.event.que_over !== undefined) queOver.value = !!msg.event.que_over
      }
      break
    case 'QUESTION_STARTED':
      question.value = msg.question
      winner.value=null
      buzzerStatus.value='QUESTION_ACTIVE'
      queOver.value=false
      break
    case 'ROUND_STATE':
      if(msg.question) question.value = msg.question
      winner.value=null
      queOver.value=false
      if(msg.round?.status) buzzerStatus.value = msg.round.status
      if(eventId.value) roundAPI.state(eventId.value).then(applyState).catch(()=>{})
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
    case 'QUE_OVER':
      queOver.value=true
      winner.value=null
      if(eventId.value) roundAPI.state(eventId.value).then(applyState).catch(()=>{})
      break
  }
}
onMounted(async ()=>{
  await load()
  ws = connectEventWS(code, { onMessage: handle })
})
onBeforeUnmount(()=>{
  if(ws) ws.close()
})
</script>

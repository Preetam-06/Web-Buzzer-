<template>
  <div class="play-page" style="min-height:100svh;display:flex;flex-direction:column;background:#080909">
    <!-- Top -->
    <div style="padding:16px 0 8px">
      <div class="container" style="display:flex;justify-content:space-between;align-items:center">
        <div style="display:flex;gap:10px;align-items:center">
          <span style="width:36px;height:36px;border-radius:10px;background:var(--primary);color:#fff;display:grid;place-items:center;font-weight:900">⚡</span>
          <div>
            <div style="font-weight:800;line-height:1">{{ participant?.team_name || 'Team' }}</div>
            <div style="font-size:12px;color:var(--muted);font-weight:600;letter-spacing:.04em;text-transform:uppercase">{{ participant?.name || 'Guest' }} • {{ eventCode }}</div>
          </div>
        </div>
        <button class="btn btn-ghost" style="padding:8px 14px;font-size:13px" @click="leave">Leave</button>
      </div>
    </div>

    <!-- Status banner -->
    <div class="container" style="margin-top:10px">
      <div :class="['card', statusColor]" style="padding:12px 16px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px">
        <div style="display:flex;gap:10px;align-items:center">
          <span class="badge" :class="badgeClass">{{ statusLabel }}</span>
          <span v-if="question" style="font-weight:600;font-size:14px;max-width:50vw;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">Q{{ question.number }}: {{ question.text }}</span>
          <span v-else style="font-size:14px;color:var(--muted)">Waiting for host to start…</span>
        </div>
        <div style="font-size:12px;color:var(--muted)">{{ connectionLabel }}</div>
      </div>
    </div>

    <!-- Center Buzzer -->
    <div style="flex:1;display:grid;place-items:center;padding:24px 16px;gap:18px">
      <div v-if="winner" class="card" style="width:min(420px,100%);text-align:center;border-color:rgba(242,238,230,.25);background:#080909">
        <div style="font-size:13px;font-weight:700;letter-spacing:.08em;color:var(--primary)">FIRST BUZZER</div>
        <div style="font-size:28px;font-weight:900;margin:6px 0">{{ winner.participant_name }}</div>
        <div style="font-weight:700;color:var(--primary)">{{ winner.team_name }}</div>
        <div v-if="isMeWinner" style="margin-top:10px" class="badge badge-success">You won! Answer now</div>
        <div v-else style="margin-top:10px" class="badge badge-muted">Buzzer locked — wait for host</div>
      </div>

      <div v-if="!winner" style="text-align:center">
        <div style="font-weight:700;color:var(--muted);letter-spacing:.06em;font-size:12px;margin-bottom:14px">{{ buzzerHint }}</div>
        <BuzzerButton :enabled="canBuzz" :loading="buzzLoading" :state="winner ? 'WINNER' : buzzerStatus" @buzz="doBuzz" />
        <div style="margin-top:16px;font-size:13px;color:var(--muted)">{{ canBuzz ? 'Tap as fast as you can!' : 'Buzzer is closed' }}</div>
      </div>
      <div v-else style="display:grid;place-items:center">
        <BuzzerButton :enabled="false" state="WINNER" />
        <div style="margin-top:12px;color:var(--muted);font-size:13px">Waiting for host to judge & reset</div>
      </div>

      <div v-if="buzzResult" :style="{background:'#080909', color: buzzResult.ok?'#4cb2e1':'#f2eee6', border:'1px solid rgba(242,238,230,.25)', padding:'10px 14px', borderRadius:'12px', fontWeight:600, fontSize:'14px'}">{{ buzzResult.msg }}</div>
    </div>

    <!-- Footer scores -->
    <div class="container" style="padding-bottom:16px">
      <div class="card" style="padding:14px">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px">
          <div style="font-weight:700">Leaderboard</div>
          <div class="badge badge-muted">{{ teams.length }} teams</div>
        </div>
        <div class="grid grid-2" style="gap:10px">
          <div v-for="t in teams" :key="t.id" style="display:flex;justify-content:space-between;align-items:center;background:#080909;border:1px solid var(--border);border-radius:12px;padding:10px 12px">
            <span style="font-weight:600">{{ t.name }}</span><span style="font-weight:800;color:var(--primary)">{{ t.score }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { useGameStore } from '../stores/game'
import { roundAPI, scoreAPI, teamAPI, eventAPI } from '../services/api'
import { connectEventWS } from '../services/websocket'
import BuzzerButton from '../components/BuzzerButton.vue'

const router = useRouter()
const store = useGameStore()
const participant = computed(()=> store.participant)
const eventCode = computed(()=> participant.value?.event_code || store.event?.code || '')

const question = ref(null)
const teams = ref([])
const buzzerStatus = ref('WAITING')
const winner = ref(null)
const buzzLoading = ref(false)
const buzzResult = ref(null)
const connectionLabel = ref('Connecting…')
let wsConn = null
let teamTimer = null

const canBuzz = computed(()=> buzzerStatus.value==='BUZZER_OPEN' && !winner.value)
const statusLabel = computed(()=>{
  const m = {WAITING:'Waiting', QUESTION_ACTIVE:'Question Active', BUZZER_OPEN:'Buzzer Open', BUZZER_LOCKED:'Buzzer Locked', ANSWERING:'Answering', COMPLETED:'Round Over'}
  return m[buzzerStatus.value] || buzzerStatus.value
})
const badgeClass = computed(()=>{
  if(buzzerStatus.value==='BUZZER_OPEN') return 'badge-success'
  if(buzzerStatus.value==='BUZZER_LOCKED') return 'badge-danger'
  return 'badge-muted'
})
const statusColor = computed(()=> '')
const buzzerHint = computed(()=>{
  if(buzzerStatus.value==='BUZZER_OPEN') return 'BUZZER IS OPEN'
  if(buzzerStatus.value==='BUZZER_LOCKED') return 'BUZZER LOCKED'
  if(buzzerStatus.value==='QUESTION_ACTIVE') return 'GET READY…'
  return 'WAITING FOR HOST'
})
const isMeWinner = computed(()=> winner.value && winner.value.participant_id===participant.value?.id)

function leave(){
  store.clearParticipant()
  if(wsConn) wsConn.close()
  router.push(`/join/${eventCode.value}`)
}

async function loadInitial(){
  if(!participant.value){ router.push('/'); return }
  try{
    const st = await roundAPI.state(participant.value.event_id || eventCode.value)
    if(st.question) question.value = st.question
    if(st.winner) winner.value = st.winner
    buzzerStatus.value = st.buzzer_status || 'WAITING'
  }catch{}
  try{
    const t = await teamAPI.list(participant.value.event_id)
    teams.value = t
  }catch{}
}

function handleMessage(msg){
  switch(msg.type){
    case 'INIT_STATE':
      if(msg.status) buzzerStatus.value = msg.status
      if(msg.winner) winner.value = msg.winner
      else if(msg.round && msg.round.winner) winner.value = msg.round.winner
      if(msg.question) question.value = msg.question
      if(msg.round) { /* round */ }
      // also event sync
      connectionLabel.value = 'Live'
      break
    case 'QUESTION_STARTED':
      question.value = msg.question
      winner.value = null
      buzzerStatus.value = 'QUESTION_ACTIVE'
      break
    case 'BUZZER_OPEN':
      buzzerStatus.value = 'BUZZER_OPEN'
      winner.value = null
      buzzResult.value = null
      break
    case 'BUZZER_WINNER':
      winner.value = msg.winner
      buzzerStatus.value = 'BUZZER_LOCKED'
      break
    case 'BUZZER_CLOSED':
      if(!winner.value) buzzerStatus.value = 'BUZZER_LOCKED'
      break
    case 'ROUND_RESET':
      winner.value = null
      buzzerStatus.value = 'WAITING'
      buzzResult.value = null
      break
    case 'SCORE_UPDATED':
      // refresh leaderboard
      if(msg.teams) teams.value = msg.teams
      else if(participant.value) teamAPI.list(participant.value.event_id).then(t=> teams.value=t)
      break
    case 'ANSWER_RESULT':
      // host judged, will reset soon
      break
  }
}

function doBuzz(){
  if(!canBuzz.value || buzzLoading.value) return
  buzzLoading.value = true
  // send via WS (critical path)
  const payload = {
    type: 'BUZZ',
    participant_id: participant.value.id,
    session_id: participant.value.session_id,
    round_id: question.value ? (store.event?.current_round_id || '') : ''
  }
  // Need round_id: get from store/event? Instead ask WS to use current; fallback fetch state
  // Safer: get round id from last INIT or QUESTION_STARTED
  // We'll store lastRoundId
  if(lastRoundId.value) payload.round_id = lastRoundId.value
  if(!payload.round_id){
    // try fetch state quickly
    roundAPI.state(participant.value.event_id).then(st=>{
      if(st.round) {
        lastRoundId.value = st.round.id
        payload.round_id = st.round.id
        wsConn.send(payload)
      }
    })
  } else {
    wsConn.send(payload)
  }
  // optimistic feedback: will get BUZZ_REJECTED or BUZZER_WINNER shortly
  setTimeout(()=> buzzLoading.value=false, 600)
}

const lastRoundId = ref(null)

onMounted(async ()=>{
  if(!participant.value){
    const raw = localStorage.getItem('participant')
    if(raw) store.setParticipant(JSON.parse(raw))
  }
  if(!participant.value){ router.replace('/'); return }
  await loadInitial()
  // listen for round id via state
  // Fetch once to get round id
  try{
    const st = await roundAPI.state(participant.value.event_id)
    if(st.round) lastRoundId.value = st.round.id
  }catch{}
  wsConn = connectEventWS(eventCode.value, {
    onOpen: ()=> connectionLabel.value='Live • Connected',
    onClose: ()=> connectionLabel.value='Reconnecting…',
    onMessage: (msg)=>{
      if(msg.round_id) lastRoundId.value = msg.round_id
      if(msg.type==='BUZZ_REJECTED'){
        buzzResult.value = {ok:false, msg: msg.reason || 'Too late — someone else buzzer first'}
        if(msg.winner) winner.value = msg.winner
      }
      if(msg.type==='BUZZER_WINNER' && msg.winner){
        // if I am winner, haptics
        if(navigator.vibrate && msg.winner.participant_id===participant.value.id) navigator.vibrate(120)
        buzzResult.value = msg.winner.participant_id===participant.value.id ? {ok:true, msg:'You won the buzzer!'} : {ok:false, msg:`${msg.winner.participant_name} won`}
      }
      handleMessage(msg)
    }
  })
  // poll leaderboard periodically (light)
  teamTimer = setInterval(async()=>{
    if(participant.value){
      try{ teams.value = await teamAPI.list(participant.value.event_id) }catch{}
    }
  }, 4000)
})
onBeforeUnmount(()=>{
  if(teamTimer) clearInterval(teamTimer)
  if(wsConn) wsConn.close()
})
</script>

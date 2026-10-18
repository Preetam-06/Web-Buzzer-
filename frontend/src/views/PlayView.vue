<template>
  <div class="play-page" style="min-height:100svh;display:flex;flex-direction:column">
    <!-- Top -->
    <div style="padding:16px 0 8px">
      <div class="container" style="display:flex;justify-content:space-between;align-items:center">
        <div style="display:flex;gap:10px;align-items:center">
          <span style="width:38px;height:38px;border-radius:12px;background:linear-gradient(145deg,#62e9ff,#0a8fb0);color:#04293a;display:grid;place-items:center;font-weight:900;box-shadow:0 0 14px rgba(0,239,255,.55)">⚡</span>
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
          <span v-if="queOver" class="badge badge-warning">QUE OVER</span>
          <span v-else-if="question" style="font-weight:600;font-size:14px;max-width:50vw;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">Q{{ question.number }}: {{ question.text }}</span>
          <span v-else style="font-size:14px;color:var(--muted)">Waiting for host to start…</span>
        </div>
        <div style="font-size:12px;color:var(--muted)">{{ connectionLabel }}</div>
      </div>
    </div>

    <!-- Center Buzzer -->
    <div style="flex:1;display:grid;place-items:center;padding:24px 16px;gap:18px">
      <div v-if="queOver" class="card" style="width:min(420px,100%);text-align:center;border-color:rgba(0,239,255,.6);box-shadow:10px 10px 24px rgba(11,53,71,.28), -10px -10px 24px rgba(255,255,255,.8), 0 0 24px rgba(0,239,255,.45)">
        <div style="font-size:13px;font-weight:800;letter-spacing:.1em;color:#0a6d8a">ALL QUESTIONS DONE</div>
        <div style="font-size:28px;font-weight:900;margin:6px 0;color:#083344">QUE OVER</div>
        <div style="font-size:13px;color:var(--muted)">Thanks for playing!</div>
      </div>

      <div v-else-if="winner" class="card" style="width:min(420px,100%);text-align:center;border-color:rgba(0,239,255,.6);box-shadow:10px 10px 24px rgba(11,53,71,.28), -10px -10px 24px rgba(255,255,255,.8), 0 0 24px rgba(0,239,255,.45)">
        <div style="font-size:13px;font-weight:800;letter-spacing:.1em;color:#0a6d8a">FIRST BUZZER</div>
        <div style="font-size:28px;font-weight:900;margin:6px 0;color:#083344">{{ winner.participant_name }}</div>
        <div style="font-weight:800;color:#0b6e8a">{{ winner.team_name }}</div>
        <div v-if="isMeWinner" style="margin-top:10px" class="badge badge-success">You won! Answer now</div>
        <div v-else style="margin-top:10px" class="badge badge-muted">Buzzer locked — wait for host</div>
      </div>

      <div v-else-if="!queOver" style="text-align:center">
        <div style="font-weight:700;color:var(--muted);letter-spacing:.06em;font-size:12px;margin-bottom:14px">{{ buzzerHint }}</div>
        <BuzzerButton :enabled="canBuzz" :loading="buzzLoading" :state="winner ? 'WINNER' : buzzerStatus" @buzz="doBuzz" />
        <div style="margin-top:16px;font-size:13px;color:var(--muted)">{{ canBuzz ? 'Tap as fast as you can!' : 'Buzzer is closed' }}</div>
      </div>
      <div v-if="!queOver && winner" style="display:grid;place-items:center">
        <BuzzerButton :enabled="false" state="WINNER" />
        <div style="margin-top:12px;color:var(--muted);font-size:13px">Waiting for host to continue</div>
      </div>

      <div v-if="buzzResult" :style="{background:'linear-gradient(145deg,rgba(255,255,255,.8),rgba(147,203,214,.5))', color: buzzResult.ok?'#0a6d8a':'#6b1020', border:'1px solid rgba(255,255,255,.7)', padding:'10px 14px', borderRadius:'14px', fontWeight:700, fontSize:'14px', boxShadow:'4px 4px 12px rgba(11,53,71,.2)'}">{{ buzzResult.msg }}</div>
    </div>
  </div>
</template>
<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { useGameStore } from '../stores/game'
import { roundAPI } from '../services/api'
import { connectEventWS } from '../services/websocket'
import BuzzerButton from '../components/BuzzerButton.vue'

const router = useRouter()
const store = useGameStore()
const participant = computed(()=> store.participant)
const eventCode = computed(()=> participant.value?.event_code || store.event?.code || '')

const question = ref(null)
const buzzerStatus = ref('WAITING')
const queOver = ref(false)
const winner = ref(null)
const buzzLoading = ref(false)
const buzzResult = ref(null)
const connectionLabel = ref('Connecting…')
let wsConn = null

const canBuzz = computed(()=> !queOver.value && buzzerStatus.value==='BUZZER_OPEN' && !winner.value)
const statusLabel = computed(()=>{
  if(queOver.value) return 'Que Over'
  const m = {WAITING:'Waiting', QUESTION_ACTIVE:'Question Active', BUZZER_OPEN:'Buzzer Open', BUZZER_LOCKED:'Buzzer Locked', ANSWERING:'Answering', COMPLETED:'Que Over'}
  return m[buzzerStatus.value] || buzzerStatus.value
})
const badgeClass = computed(()=>{
  if(queOver.value) return 'badge-warning'
  if(buzzerStatus.value==='BUZZER_OPEN') return 'badge-success'
  if(buzzerStatus.value==='BUZZER_LOCKED') return 'badge-danger'
  return 'badge-muted'
})
const statusColor = computed(()=> '')
const buzzerHint = computed(()=>{
  if(queOver.value) return 'QUE OVER'
  if(buzzerStatus.value==='BUZZER_OPEN') return 'BUZZER IS OPEN'
  if(buzzerStatus.value==='BUZZER_LOCKED') return 'BUZZER LOCKED'
  if(buzzerStatus.value==='QUESTION_ACTIVE') return 'GET READY…'
  return 'WAITING FOR HOST'
})
const isMeWinner = computed(()=> winner.value && winner.value.participant_id===participant.value?.id)
let localAudioContext = null

function prepareLocalWinnerSound(){
  const AudioContext = window.AudioContext || window.webkitAudioContext
  if(!AudioContext) return
  if(!localAudioContext) localAudioContext = new AudioContext()
  localAudioContext.resume().catch(()=>{})
}

function playLocalWinnerSound(){
  if(!localAudioContext) return
  const oscillator = localAudioContext.createOscillator()
  const gain = localAudioContext.createGain()
  const now = localAudioContext.currentTime

  oscillator.type = 'square'
  oscillator.frequency.setValueAtTime(880, now)
  oscillator.frequency.exponentialRampToValueAtTime(220, now + 0.18)
  gain.gain.setValueAtTime(0.0001, now)
  gain.gain.exponentialRampToValueAtTime(0.18, now + 0.01)
  gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.2)
  oscillator.connect(gain)
  gain.connect(localAudioContext.destination)
  oscillator.start(now)
  oscillator.stop(now + 0.2)
}

function leave(){
  store.clearParticipant()
  if(wsConn) wsConn.close()
  router.push(`/join/${eventCode.value}`)
}

function applyState(st){
  if(!st) return
  if(st.question !== undefined) question.value = st.question
  if(st.winner !== undefined) winner.value = st.winner
  if(st.buzzer_status) buzzerStatus.value = st.buzzer_status
  if(st.que_over !== undefined) queOver.value = !!st.que_over
}

async function loadInitial(){
  if(!participant.value){ router.push('/'); return }
  try{
    const st = await roundAPI.state(participant.value.event_id || eventCode.value)
    applyState(st)
  }catch{}
}

function handleMessage(msg){
  switch(msg.type){
    case 'INIT_STATE':
      if(msg.status) buzzerStatus.value = msg.status
      if(msg.winner) winner.value = msg.winner
      else if(msg.round && msg.round.winner) winner.value = msg.round.winner
      if(msg.question) question.value = msg.question
      if(msg.event?.que_over !== undefined) queOver.value = !!msg.event.que_over
      connectionLabel.value = 'Live'
      break
    case 'QUESTION_STARTED':
      question.value = msg.question
      winner.value = null
      buzzerStatus.value = 'QUESTION_ACTIVE'
      queOver.value = false
      break
    case 'ROUND_STATE':
      if(msg.question) question.value = msg.question
      winner.value = null
      queOver.value = false
      if(msg.round?.status) buzzerStatus.value = msg.round.status
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
    case 'QUE_OVER':
      queOver.value = true
      winner.value = null
      buzzResult.value = null
      break
  }
}

function doBuzz(){
  if(!canBuzz.value || buzzLoading.value) return
  buzzLoading.value = true
  prepareLocalWinnerSound()
  const payload = {
    type: 'BUZZ',
    participant_id: participant.value.id,
    session_id: participant.value.session_id,
    round_id: question.value ? (store.event?.current_round_id || '') : ''
  }
  if(lastRoundId.value) payload.round_id = lastRoundId.value
  if(!payload.round_id){
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
        const isLocalWinner = msg.winner.participant_id===participant.value.id
        if(isLocalWinner){
          if(navigator.vibrate) navigator.vibrate(120)
          playLocalWinnerSound()
        }
        buzzResult.value = isLocalWinner ? {ok:true, msg:'You won the buzzer!'} : {ok:false, msg:`${msg.winner.participant_name} won`}
      }
      handleMessage(msg)
    }
  })
})
onBeforeUnmount(()=>{
  if(wsConn) wsConn.close()
})
</script>

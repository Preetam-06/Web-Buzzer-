<template>
  <div class="join-page" style="min-height:100vh;display:flex;flex-direction:column">
    <div class="topbar" style="padding:14px 0">
      <div class="container" style="display:flex;justify-content:space-between;align-items:center">
        <div style="font-weight:800;display:flex;gap:8px;align-items:center"><span style="background:var(--primary);color:#fff;width:34px;height:34px;border-radius:10px;display:grid;place-items:center">⚡</span> Faculty Buzzer</div>
        <div class="badge badge-muted">{{ code }}</div>
      </div>
    </div>

    <div class="container" style="flex:1;display:grid;place-items:center;padding:24px 16px">
      <div v-if="loadingEvent" class="card" style="width:min(480px,100%);text-align:center">Loading event...</div>

      <div v-else-if="!event" class="card" style="width:min(480px,100%);text-align:center">
        <h2>Invalid event</h2>
        <p style="color:var(--muted)">Check QR code / event code.</p>
      </div>

      <div v-else class="card" style="width:min(480px,100%)">
        <h2 style="margin:0 0 6px">{{ event.name }}</h2>
        <p style="color:var(--muted);margin-bottom:18px;font-size:14px">Enter your name and choose your team to join.</p>

        <div v-if="alreadyJoined" style="text-align:center;padding:12px 0">
          <div style="font-weight:700;margin-bottom:8px">You're joined as {{ alreadyJoined.name }} ({{ alreadyJoined.team_name }})</div>
          <button class="btn btn-primary" style="width:100%" @click="$router.push('/play')">Go to Buzzer →</button>
          <button class="btn btn-ghost" style="width:100%;margin-top:8px" @click="clearAndRejoin">Join as different person</button>
        </div>

        <form v-else @submit.prevent="doJoin" style="display:grid;gap:14px">
          <div>
            <label class="label">Your Name</label>
            <input v-model="name" class="input" placeholder="e.g., Preetam" maxlength="40" required />
          </div>
          <div>
            <label class="label">Select Team</label>
            <div v-if="teams.length===0" style="color:var(--muted);font-size:14px">No teams yet — wait for host to create teams.</div>
            <div v-else class="grid" style="gap:10px">
              <button v-for="t in teams" :key="t.id" type="button" @click="teamId=t.id" :class="['btn', teamId===t.id ? 'btn-primary':'btn-ghost']" style="justify-content:space-between">
                <span>{{ t.name }}</span><span class="badge badge-muted">{{ t.member_count }} joined</span>
              </button>
            </div>
          </div>

          <div v-if="error" style="background:#080909;color:#f2eee6;padding:10px 12px;border:1px solid var(--border);font-size:14px">{{ error }}</div>

          <button class="btn btn-primary btn-lg" :disabled="!name.trim() || !teamId || joining" type="submit">
            {{ joining ? 'Joining...' : 'Join Event' }}
          </button>

          <div style="display:flex;gap:8px;justify-content:center;font-size:13px;color:var(--muted)">
            <span>{{ participantsCount }}/{{ event.max_participants }} joined</span><span>•</span><span>Event: {{ event.code }}</span>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>
<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { eventAPI, teamAPI, participantAPI } from '../services/api'
import { useGameStore } from '../stores/game'

const props = defineProps({ code:String })
const route = useRoute()
const router = useRouter()
const store = useGameStore()

const code = props.code || route.params.code
const event = ref(null)
const teams = ref([])
const participantsCount = ref(0)
const name = ref('')
const teamId = ref('')
const error = ref('')
const joining = ref(false)
const loadingEvent = ref(true)

const alreadyJoined = computed(()=>{
  const p = store.participant
  if(p && p.event_id===event.value?.id) return p
  return null
})

async function load(){
  try{
    event.value = await eventAPI.get(code)
    const t = await teamAPI.list(event.value.id)
    teams.value = t
    if(t.length>0) teamId.value = t[0].id
    const parts = await participantAPI.list(event.value.id)
    participantsCount.value = parts.length
    store.event = event.value
  }catch(e){
    event.value = null
  }finally{ loadingEvent.value=false }
}
function clearAndRejoin(){
  store.clearParticipant()
  name.value=''
}
async function doJoin(){
  error.value=''
  if(!name.value.trim()){ error.value='Name required'; return }
  if(!teamId.value){ error.value='Pick a team'; return }
  joining.value=true
  try{
    const p = await participantAPI.join(code, { name: name.value.trim(), team_id: teamId.value })
    // enrich with event info
    const full = { ...p, event_code: code, event_id: event.value.id }
    store.setParticipant(full)
    router.push('/play')
  }catch(e){
    error.value = e.response?.data?.detail || e.message || 'Join failed'
  }finally{ joining.value=false }
}
onMounted(load)
</script>

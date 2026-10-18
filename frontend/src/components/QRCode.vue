<template>
  <div class="card" style="display:flex;flex-direction:column;align-items:center;gap:12px">
    <img v-if="qrSrc" :src="qrSrc" alt="QR" style="width:200px;height:200px;image-rendering:pixelated;border-radius:18px;border:1px solid rgba(255,255,255,.8);background:#fff;padding:8px;box-shadow:6px 6px 16px rgba(11,53,71,.22), -6px -6px 16px rgba(255,255,255,.7)"/>
    <div style="font-weight:800;color:#083344">{{ code }}</div>
    <div style="font-size:13px;color:#3d6f80;word-break:break-all;text-align:center">{{ joinUrl }}</div>
    <div v-if="lanIp && lanIp!=='localhost'" style="font-size:11px;color:#0a6d8a;font-weight:700">LAN IP: {{ lanIp }} — phones on same Wi-Fi can scan</div>
    <div v-else-if="lanIp==='localhost'" style="font-size:11px;color:#8a4a00;font-weight:700">⚠️ LAN IP not detected — connect the host to Wi-Fi and restart the app</div>
    <a :href="joinUrl" target="_blank" class="btn btn-ghost" style="width:100%">Open Join Link</a>
    <button class="btn btn-ghost" style="width:100%;font-size:12px" @click="copyLink">📋 Copy Link</button>
  </div>
</template>
<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import api from '../services/api'
const props = defineProps({ code:String, eventId:String })
const joinUrl = ref('')
const lanIp = ref('')
const baseUrl = ref('')
const qrSrc = computed(()=> baseUrl.value
  ? `/api/events/${props.eventId||props.code}/qr?base_url=${encodeURIComponent(baseUrl.value)}`
  : '')

function frontendOrigin(ip){
  const port = location.port
  const suffix = port ? `:${port}` : ''
  return `${location.protocol}//${ip}${suffix}`
}

async function fetchJoinUrl(){
  try{
    const network = await api.get('/api/network-info')
    lanIp.value = network.data.lan_ip || ''
    baseUrl.value = lanIp.value && lanIp.value !== 'localhost'
      ? frontendOrigin(lanIp.value)
      : location.origin
    const { data } = await api.get(`/api/events/${props.eventId||props.code}/qr-url`, {
      params: { base_url: baseUrl.value }
    })
    if(data.url && data.url.startsWith('http')){
      joinUrl.value = data.url
    }
  }catch{
    baseUrl.value = location.origin
    joinUrl.value = `${location.origin}/join/${props.code}`
  }
}
function copyLink(){
  navigator.clipboard.writeText(joinUrl.value)
}

onMounted(fetchJoinUrl)
watch(()=> props.code, fetchJoinUrl)
watch(()=> props.eventId, fetchJoinUrl)
</script>

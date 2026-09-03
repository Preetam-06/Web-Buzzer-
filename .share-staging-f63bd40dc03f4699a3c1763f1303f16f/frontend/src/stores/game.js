import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useGameStore = defineStore('game', ()=>{
  const event = ref(null)
  const participant = ref(JSON.parse(localStorage.getItem('participant')||'null'))
  const round = ref(null)
  const question = ref(null)
  const winner = ref(null)
  const buzzerStatus = ref('WAITING')

  function setParticipant(p){
    participant.value = p
    if(p) localStorage.setItem('participant', JSON.stringify(p))
  }
  function clearParticipant(){
    participant.value=null
    localStorage.removeItem('participant')
  }
  return { event, participant, round, question, winner, buzzerStatus, setParticipant, clearParticipant }
})

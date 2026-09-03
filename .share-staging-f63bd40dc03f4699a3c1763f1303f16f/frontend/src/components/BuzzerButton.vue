<template>
  <button
    class="buzzer-btn"
    :class="{ pulse: enabled }"
    :disabled="!enabled || loading"
    @click="$emit('buzz')"
    @touchstart.prevent="$emit('buzz')"
  >
    <span v-if="loading">...</span>
    <span v-else-if="state==='WINNER'">WINNER</span>
    <span v-else-if="!enabled">LOCKED</span>
    <span v-else>BUZZ</span>
  </button>
</template>
<script setup>
defineProps({
  enabled:Boolean,
  loading:Boolean,
  state:String
})
defineEmits(['buzz'])
</script>

export function connectEventWS(eventCode, handlers){
  const proto = location.protocol === 'https:' ? 'wss:' : 'ws:'
  const url = `${proto}//${location.host}/ws/event/${eventCode}`
  let ws = null
  let closed = false
  let retry = 0
  let retryTimer = null
  function open(){
    ws = new WebSocket(url)
    ws.onopen = ()=>{ retry=0; handlers.onOpen && handlers.onOpen() }
    ws.onmessage = (e)=>{
      try{
        const msg = JSON.parse(e.data)
        handlers.onMessage && handlers.onMessage(msg)
      }catch{}
    }
    ws.onclose = ()=>{
      handlers.onClose && handlers.onClose()
      if(!closed && retry < 10){
        retryTimer = setTimeout(()=>{ retry++; open() }, 1000 + retry*400)
      }
    }
    ws.onerror = ()=>{ handlers.onError && handlers.onError() }
  }
  open()
  return {
    send: (obj)=>{ try{ if(ws && ws.readyState === WebSocket.OPEN) ws.send(JSON.stringify(obj)) }catch{} },
    close: ()=>{ closed=true; if(retryTimer) clearTimeout(retryTimer); try{ ws?.close() }catch{} },
    get ws(){ return ws }
  }
}

export function ping (socket: any) {
  socket.send(JSON.stringify({ ok: true }))
}

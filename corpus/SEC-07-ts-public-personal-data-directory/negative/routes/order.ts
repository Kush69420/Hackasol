import fs from 'fs'
import path from 'path'
export function placeOrder() { return (req, res) => {
  const email = req.body.email
  const stream = fs.createWriteStream(path.join('private/', 'order.pdf'))
  stream.write(email)
  res.json({ ok: true })
} }

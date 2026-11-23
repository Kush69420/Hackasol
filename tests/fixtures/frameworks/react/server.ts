import express from 'express'
import { create } from './routes/users'
import { prisma } from './lib/db'

const app = express()
app.post('/api/users', create())
app.post('/api/leads', async (req: any, res: any) => {
  await prisma.lead.create({ data: { email: req.body.email } })
  res.json({ ok: true })
})

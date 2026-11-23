import express from 'express'
import mongoose from 'mongoose'
import { create } from './routes/users'
import Ghost from './routes/ghost'
const Lead = require('./models/Lead')

mongoose.connect(process.env.MONGO_URL as string)
const app = express()
app.post('/api/users', create())
app.post('/api/leads', async (req: any, res: any) => {
  await new Lead(req.body).save()
  await Ghost.create({ email: req.body.email })
  res.json({ ok: true })
})

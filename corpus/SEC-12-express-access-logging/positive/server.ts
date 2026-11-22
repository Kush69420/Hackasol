import express from 'express'
import { User } from './models/user'
const app = express()
app.get('/accounts', async (req, res) => { const records = await User.findAll(); res.json(records) })

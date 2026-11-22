import express from 'express'
import morgan from 'morgan'
import { User } from './models/user'
const app = express()
app.use(morgan('combined'))
app.get('/accounts', async (req, res) => { const records = await User.findAll(); res.json(records) })

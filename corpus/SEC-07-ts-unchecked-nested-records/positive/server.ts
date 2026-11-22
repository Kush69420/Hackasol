import express from 'express'
import cors from 'cors'
import { listMemories } from './routes/list'
const app = express()
app.use(cors())
app.get('/records', listMemories())

import express from 'express'
import * as security from './lib/insecurity'
import { lookup } from './routes/lookup'
const app = express()
app.post('/lookup', lookup())

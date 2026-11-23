import express from 'express'
import * as security from './lib/insecurity'
import { getRecord } from './routes/record'
const app = express()
app.get('/records/:id', getRecord())

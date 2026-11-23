import express from 'express'
import * as security from './lib/insecurity'
import { getRecord, countRecords, sampleRecords } from './routes/record'
const app = express()
app.get('/records/:id', security.appendUserId(), getRecord())
app.get('/count/:id', countRecords())
app.get('/sample/:id', sampleRecords())

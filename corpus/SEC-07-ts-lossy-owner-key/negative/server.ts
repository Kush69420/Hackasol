import express from 'express'
import * as security from './lib/insecurity'
import { guardedHistory } from './routes/guarded'
import { history } from './routes/history'
const app = express()
app.get('/history', security.isAuthorized(), history())
app.get('/guarded-history', security.isAuthorized(), guardedHistory())

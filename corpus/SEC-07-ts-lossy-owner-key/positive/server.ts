import express from 'express'
import * as security from './lib/insecurity'
import { history } from './routes/history'
const app = express()
app.get('/history', security.isAuthorized(), history())

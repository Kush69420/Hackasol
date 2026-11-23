import express from 'express'
import * as security from './lib/insecurity'
import { listAccounts } from './routes/list'
const app = express()
app.get('/records', security.isAuthorized(), listAccounts())

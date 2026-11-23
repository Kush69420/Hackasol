import express from 'express'
import * as security from './lib/insecurity'
import { listAccounts, countAccounts, sampleAccounts } from './routes/list'
const app = express()
app.get('/records', security.isAuthorized(), security.appendUserId(), listAccounts())
app.get('/count', security.isAuthorized(), countAccounts())
app.get('/sample', security.isAuthorized(), sampleAccounts())

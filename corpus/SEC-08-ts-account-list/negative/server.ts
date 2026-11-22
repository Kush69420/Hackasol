import express from 'express'
import cors from 'cors'
import { listAccounts } from './routes/list'
const app = express()
app.use(cors())
app.get('/records', security.isAuthorized(), listAccounts())

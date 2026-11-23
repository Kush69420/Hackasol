import express from 'express'
import * as security from './lib/insecurity'
import { profile } from './routes/profile'
const app = express()
app.get('/profile/:id', security.isAuthorized(), profile())

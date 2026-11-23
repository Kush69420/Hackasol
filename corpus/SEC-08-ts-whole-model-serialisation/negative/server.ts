import express from 'express'
import * as security from './lib/insecurity'
import { profile, sampleProfiles, countProfiles } from './routes/profile'
const app = express()
app.get('/profile/:id', security.isAuthorized(), profile())
app.get('/sample', security.isAuthorized(), sampleProfiles())
app.get('/count', security.isAuthorized(), countProfiles())

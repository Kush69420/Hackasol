import express from 'express'
import * as security from './lib/insecurity'
import serveIndex from 'serve-index'
import { placeOrder } from './routes/order'
const app = express()
app.use('/files', security.isAuthorized(), serveIndex('files', { icons: true }))
app.post('/order', placeOrder())

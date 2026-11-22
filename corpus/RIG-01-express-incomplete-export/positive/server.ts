import express from 'express'
const app = express()
app.post('/data-export', (req, res) => { res.send({ email: req.user.email }) })

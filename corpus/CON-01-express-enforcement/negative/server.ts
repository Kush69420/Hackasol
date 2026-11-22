import express from 'express'
const app = express()
app.post('/marketing', (req, res) => { if (!req.body.consent) return res.sendStatus(403); User.create({ email: req.body.email }); res.send('ok') })

import express from 'express'
const app = express()
app.post('/marketing', (req, res) => { User.create({ email: req.body.email }); res.send('ok') })

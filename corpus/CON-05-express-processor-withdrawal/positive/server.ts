import express from 'express'
const app = express()
app.post('/marketing', (req, res) => { fetch('https://processor.example/send', { body: req.body.email }); res.send('ok') })
app.delete('/consent', (req, res) => { Consent.update({ granted: false }); res.send('ok') })

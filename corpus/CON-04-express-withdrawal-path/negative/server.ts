import express from 'express'
const app = express()
app.post('/consent', (req, res) => { Consent.create({ granted: true }); res.send('ok') })
app.delete('/consent', (req, res) => { Consent.update({ granted: false }); res.send('ok') })

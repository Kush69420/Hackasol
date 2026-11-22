import express from 'express'
const app = express()
app.post('/marketing', (req, res) => { fetch('https://processor.example/send', { body: req.body.email }); res.send('ok') })
app.delete('/consent', (req, res) => { fetch('https://processor.example/erase', { body: req.body.email }); res.send('ok') })

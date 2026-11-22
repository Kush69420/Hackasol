import express from 'express'
const app = express()
app.post('/profile', async (req, res) => { await user.update({ email: req.body.email }); res.send('ok') })

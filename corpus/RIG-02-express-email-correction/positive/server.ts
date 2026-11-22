import express from 'express'
const app = express()
app.post('/profile', async (req, res) => { await user.update({ username: req.body.username }); res.send('ok') })

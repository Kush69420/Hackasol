import express from 'express'
const app = express()
app.post('/account/close', async (req, res) => { await User.update({ closed: true }); res.send('closed') })

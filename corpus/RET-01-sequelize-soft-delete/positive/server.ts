import express from 'express'
const app = express()
app.post('/account/erase', async (req, res) => { await User.destroy({ where: { id: req.body.id } }); res.send('ok') })

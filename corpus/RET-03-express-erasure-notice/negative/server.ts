import express from 'express'
const app = express()
app.delete('/account/delete', async (req, res) => { await sendNotice(req.body.id); await delay(48 * 60 * 60 * 1000); await User.destroy({ where: { id: req.body.id } }); res.send('deleted') })

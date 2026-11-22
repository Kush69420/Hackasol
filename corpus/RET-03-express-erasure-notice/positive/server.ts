import express from 'express'
const app = express()
app.delete('/account/delete', async (req, res) => { await User.destroy({ where: { id: req.body.id } }); res.send('deleted') })

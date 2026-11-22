import express from 'express'
const app = express()
app.post('/dataerasure', async (req, res) => { await PrivacyRequestModel.create({ deletionRequested: true }); await User.destroy({ where: { id: req.user.id } }); res.send('done') })

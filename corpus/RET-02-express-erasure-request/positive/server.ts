import express from 'express'
const app = express()
app.post('/dataerasure', async (req, res) => { await PrivacyRequestModel.create({ deletionRequested: true }); res.send('received') })

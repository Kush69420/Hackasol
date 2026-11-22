import express from 'express'
const app = express()
app.get('/account', (req, res) => {
  try { throw new Error(req.body.email) } catch (error) { res.send('Unable to process request') }
})

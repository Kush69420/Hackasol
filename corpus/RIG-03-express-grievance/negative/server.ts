import express from 'express'
const app = express()
app.post('/api/complaints', (req, res) => { Complaint.create(req.body); res.send('received') })

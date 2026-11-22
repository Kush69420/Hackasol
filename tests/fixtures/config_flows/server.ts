const access = getStream({ filename: 'logs/access.%DATE%', frequency: 'daily', max_logs: '14' })
app.get('/before', (req, res) => res.send(req.query.value))
app.use(morgan('combined', { stream: access }))
app.get('/after', (req, res) => res.send(req.query.value))

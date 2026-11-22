import { change } from './routes/account'
const app = express()
const accessLogStream = getStream({ filename: 'access.log', frequency: 'daily', max_logs: '2d' })
app.use(morgan('combined', { stream: accessLogStream }))
app.get('/password', change())

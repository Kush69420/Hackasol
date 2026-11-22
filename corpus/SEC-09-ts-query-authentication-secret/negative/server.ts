import { change } from './routes/account'
const app = express()
app.use(morgan('combined'))
app.post('/password', change())

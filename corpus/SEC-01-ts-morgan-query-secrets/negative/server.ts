import { change } from './routes/account'
const app = express()
app.use(morgan(':method :status'))
app.get('/password', change())

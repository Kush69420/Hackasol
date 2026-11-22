import * as handlers from './routes/handlers'
import { create } from './routes/handlers'
import router from './routes/router'
const app = express()
app.use(morgan('combined', { stream: accessLogStream }))
const accessLogStream = getStream({ filename: 'access.log', frequency: 'daily', max_logs: '2d', date_format: 'YYYY-MM-DD' })
app.use('/api/Users/:id', security.isAuthorized())
app.get('/before', handlers.show())
app.post('/before', create())
app.put('/before', handlers.show())
app.delete('/before', handlers.show())
app.patch('/before', handlers.show())
app.route('/chain').get(handlers.show()).post(create())
app.use('/mounted', router)
const autoModels = [{ name: 'User', exclude: ['password'], model: UserModel, include: [OtherModel] }]
finale.initialize({ app })
for (const { name, exclude, model, include } of autoModels) {
  finale.resource({ model, endpoints: [`/api/${name}s`, `/api/${name}s/:id`], excludeAttributes: exclude, include })
}

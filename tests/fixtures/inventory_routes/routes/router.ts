import { show } from './handlers'
const router = express.Router()
router.use(security.isAuthorized())
router.get('/thing', show())
export default router

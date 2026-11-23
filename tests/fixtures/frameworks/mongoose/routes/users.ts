import User from '../models/User'
import { Staff } from '../models/Staff'

export function create() {
  return async (req: any, res: any) => {
    await User.create({ email: req.body.email })
    await Staff.create({ name: req.body.name })
    res.json({ ok: true })
  }
}

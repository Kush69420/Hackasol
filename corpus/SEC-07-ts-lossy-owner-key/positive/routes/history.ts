import { UserModel } from '../models/user'
export function history() { return async (req, res) => {
  const email = req.query.email
  const masked = email.replace(/[aeiou]/gi, '*')
  const rows = await UserModel.findAll({ where: { email: masked } })
  res.json(rows)
} }

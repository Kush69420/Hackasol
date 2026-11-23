import { UserModel } from '../models/user'
export function profile() { return async (req, res) => {
  const user = await UserModel.findByPk(req.params.id)
  res.json({ user })
} }

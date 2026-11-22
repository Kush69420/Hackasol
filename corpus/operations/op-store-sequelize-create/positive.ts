import { UserModel } from '../../models/user'

export async function register (req: any) {
  const user = await UserModel.create({ email: req.body.email, password: req.body.password })
  return user
}

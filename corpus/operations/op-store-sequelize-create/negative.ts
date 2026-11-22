import { UserModel } from '../../models/user'

export async function lookup (email: string, payload: any) {
  const user = await UserModel.findOne({ where: { email } })
  await UserModel.create(payload)
  return user
}

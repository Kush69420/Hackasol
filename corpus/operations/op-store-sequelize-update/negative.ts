import { UserModel } from '../../models/user'

export async function changeEmail (id: number, changes: object) {
  await UserModel.update(changes, { where: { id } })
  const user = await UserModel.findByPk(id)
  return user?.get('email')
}

import { UserModel } from '../models/user'
export function listAccounts() { return async (req, res) => {
  const records = await UserModel.findAll()
  res.json({ status: 'success', data: records.map(record => ({ ...record.dataValues, password: '*' })) })
} }

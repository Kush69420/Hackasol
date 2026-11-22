import { UserModel } from '../models/user'
export function listAccounts() { return async (req, res) => {
 const records = await UserModel.findAll({ attributes: ["id"] })
 res.json(records.map(record => ({ ...record.dataValues, password: record.password.replace(/./g, '*'), totpSecret: record.totpSecret.replace(/./g, '*') })))
} }

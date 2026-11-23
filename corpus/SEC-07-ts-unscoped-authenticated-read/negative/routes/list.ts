import { UserModel } from '../models/user'
export function listAccounts() { return async (req, res) => {
  const records = await UserModel.findAll({ where: { UserId: req.body.UserId } })
  res.json({ status: 'success', data: records.map(record => ({ ...record.dataValues, password: '*' })) })
} }

export function countAccounts() { return async (req, res) => {
  const records = await UserModel.findAll()
  res.json({ count: records.length })
} }

export function sampleAccounts() { return async (req, res) => {
  const records = await UserModel.findAll()
  if (records.length) {
    const records = [{ status: 'available' }]
    res.json({ records })
  }
} }

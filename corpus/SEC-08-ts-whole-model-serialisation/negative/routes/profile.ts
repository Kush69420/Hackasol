import { UserModel } from '../models/user'
export function profile() { return async (req, res) => {
  const user = await UserModel.findByPk(req.params.id, { attributes: ['id'] })
  res.json({ user })
} }

export function sampleProfiles() { return async (req, res) => {
  const users = await UserModel.findAll()
  if (users.length) {
    const users = [{ status: 'available' }]
    res.json({ users })
  }
} }

export function countProfiles() { return async (req, res) => {
  const users = await UserModel.findAll()
  res.json({ count: users.length })
} }

const config = { query: ['status'] }
const record = { status: 'available' }
for (const key of config.query) {
  console.log(record[key])
}

import { UserModel } from '../models/user'
export function getRecord() { return (req, res) => {
  UserModel.findAll({ where: { id: JSON.parse(req.params.id), UserId: req.body.UserId } }).then((rows) => {
    return res.send(rows)
  })
} }

export function countRecords() { return (req, res) => {
  return UserModel.findAll({ where: { id: JSON.parse(req.params.id) } }).then((rows) => {
    return res.json({ count: rows.length })
  })
} }

export function sampleRecords() { return (req, res) => {
  return UserModel.findAll({ where: { id: JSON.parse(req.params.id) } }).then((rows) => {
    if (rows.length) {
      const rows = [{ status: 'available' }]
      return res.json({ rows })
    }
  })
} }

import { UserModel } from '../models/user'
export function getRecord() { return (req, res) => {
  UserModel.findAll({ where: { id: JSON.parse(req.params.id) } }).then((rows) => {
    return res.send(rows)
  })
} }

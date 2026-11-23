import * as security from '../lib/insecurity'
import { OrderModel } from '../models/order'
import { UserModel } from '../models/user'

export function guardedHistory() { return async (req, res) => {
  const principal = security.authenticatedUsers.get(req.cookies.token)
  if (!principal) return res.sendStatus(401)
  const address = principal.data.email
  const masked = address.replace(/[aeiou]/gi, '*')
  const prefix = security.hash(address).slice(0, 4) + '-'
  const accounts = await UserModel.findAll({ paranoid: false })
  if (accounts.some(other => other.id !== principal.data.id && other.email &&
      other.email.replace(/[aeiou]/gi, '*') === masked &&
      security.hash(other.email).slice(0, 4) + '-' === prefix)) {
    return res.sendStatus(409)
  }
  const rows = await OrderModel.findAll({ where: { email: masked } })
  const owned = rows.filter(record => record.lookupCode.startsWith(prefix))
  res.json(owned)
} }

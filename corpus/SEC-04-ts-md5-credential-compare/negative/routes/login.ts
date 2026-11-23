import * as security from '../lib/security'
export const login = () => (req, res) => {
  db.query(`SELECT * FROM Users WHERE password = '${bcrypt.hashSync(req.body.password, 12)}'`)
  res.set('ETag', security.etag(req.body.email))
}

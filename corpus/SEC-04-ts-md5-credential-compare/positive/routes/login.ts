import * as security from '../lib/security'
export const login = () => (req, res) => {
  db.query(`SELECT * FROM Users WHERE password = '${security.hash(req.body.password || '')}'`)
}

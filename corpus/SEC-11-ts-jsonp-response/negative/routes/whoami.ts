export const whoami = () => (req, res) => {
  res.json({ email: req.user.email })
}
export const version = () => (req, res) => res.jsonp({ build: '1' })

export const whoami = () => (req, res) => {
  const body = { email: req.user.email }
  if (req.query.callback === undefined) res.json(body)
  else res.jsonp(body)
}

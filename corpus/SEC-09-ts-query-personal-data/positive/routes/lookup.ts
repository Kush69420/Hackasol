export function lookup() { return (req, res) => {
  const email = req.query.email
  res.json({ found: Boolean(email) })
} }

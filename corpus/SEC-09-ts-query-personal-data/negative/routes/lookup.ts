export function lookup() { return (req, res) => {
  const email = req.body.email
  const page = req.query.page
  res.json({ found: Boolean(email), page })
} }

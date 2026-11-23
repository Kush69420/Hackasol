export const status = (req, res) => {
  console.log(req.user.email)
  res.jsonp({ ok: true })
}

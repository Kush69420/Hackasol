export function lookup() {
  return (req: any, res: any) => {
    res.json({ email: req.params.email })
  }
}

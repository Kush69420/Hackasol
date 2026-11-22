export function failed (err: any, req: any, res: any, user: any) {
  res.status(500).send(`Could not save ${user.email}: ${err.message}`)
}

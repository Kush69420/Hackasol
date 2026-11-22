export function currentUser (req: any, res: any, user: any) {
  res.json({ user: { id: user.id, email: user.email } })
}

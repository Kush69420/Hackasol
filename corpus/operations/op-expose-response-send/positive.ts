export function profile (req: any, res: any, user: any) {
  res.status(200).send({ email: user.email })
}

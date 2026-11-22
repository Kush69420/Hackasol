export function page (req: any, res: any, user: any) {
  res.render('profile', { email: user.email })
}

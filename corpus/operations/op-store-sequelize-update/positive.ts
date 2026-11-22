export async function changeEmail (user: any, req: any) {
  await user.update({ email: req.body.email })
}

export function clientOrigin (req: any) {
  return req.get('x-forwarded-for')
}

export function failed (err: any, req: any, res: any) {
  res.status(500).send('Something went wrong.')
}

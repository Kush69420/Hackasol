import { prisma } from '../lib/db'

export function create() {
  return async (req: any, res: any) => {
    const { email, phone } = req.body
    await prisma.user.create({ data: { email, phone } })
    res.json({ ok: true })
  }
}

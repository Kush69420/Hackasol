import { prisma } from '../lib/db'

const local = { customer: { create(_: unknown) { return null } } }

export function nearMiss(email: string) {
  prisma.customer.create({ data: { email } })
  local.customer.create({ data: { email } })
}

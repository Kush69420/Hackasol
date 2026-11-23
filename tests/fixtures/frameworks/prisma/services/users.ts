import { prisma } from '../lib/db'

export async function register(input: { email: string; phone: string }) {
  return prisma.user.create({ data: { email: input.email, phone: input.phone } })
}

export async function findUser(id: number) {
  return prisma.user.findUnique({ where: { id } })
}

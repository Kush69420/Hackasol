import { UserModel } from '../models/user'
import { MemoryModel } from '../models/memory'
export function listMemories() { return async (req, res) => {
 const records = await MemoryModel.findAll({ include: [UserModel], where: { UserId: req.user.id } })
 res.json(records)
} }

import mongoose from 'mongoose'

const staffSchema = new mongoose.Schema({ email: String, name: String })
export const Staff = mongoose.model('Staff', staffSchema)

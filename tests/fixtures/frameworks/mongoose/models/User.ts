import mongoose from 'mongoose'

const userSchema = new mongoose.Schema({
  email: { type: String, required: true },
  phone: String,
  address: { city: String }
})

export default mongoose.model('User', userSchema)

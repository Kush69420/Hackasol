const mongoose = require('mongoose')
const leadSchema = new mongoose.Schema({ email: String })
module.exports = mongoose.model('Lead', leadSchema)

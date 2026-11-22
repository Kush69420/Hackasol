User.init({ password: { type: DataTypes.STRING, set (password: string) { this.setDataValue('password', bcrypt.hash(password)) } } }, { sequelize })
const etag = (value: string) => crypto.createHash('md5').update(value).digest('hex')

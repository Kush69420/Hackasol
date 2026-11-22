User.init({ password: { type: DataTypes.STRING, set (password: string) { this.setDataValue('password', hash(password)) } } }, { sequelize })
const hash = (value: string) => crypto.createHash('md5').update(value).digest('hex')

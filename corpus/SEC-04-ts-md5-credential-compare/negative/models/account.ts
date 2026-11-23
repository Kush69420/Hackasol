User.init({ password: { type: DataTypes.STRING, set (password: string) { this.setDataValue('password', bcrypt.hashSync(password, 12)) } } }, { sequelize })

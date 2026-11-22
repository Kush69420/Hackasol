Thing.init({
  email: { type: DataTypes.STRING, allowNull: false, unique: true, validate: { isEmail: true } },
  password: { type: DataTypes.STRING, defaultValue: '' }
}, { tableName: 'Things', paranoid: true, sequelize })

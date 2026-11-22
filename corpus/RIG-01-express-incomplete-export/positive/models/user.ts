import { Model, DataTypes } from 'sequelize'
class User extends Model {}
User.init({ email: { type: DataTypes.STRING }, lastLoginIp: { type: DataTypes.STRING } }, { sequelize })

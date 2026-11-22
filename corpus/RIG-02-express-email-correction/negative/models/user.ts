import { Model, DataTypes } from 'sequelize'
class User extends Model {}
User.init({ email: { type: DataTypes.STRING }, username: { type: DataTypes.STRING } }, { sequelize })

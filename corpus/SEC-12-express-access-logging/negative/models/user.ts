import { Model, DataTypes } from 'sequelize'
export class User extends Model {}
User.init({ email: { type: DataTypes.STRING } }, { sequelize })

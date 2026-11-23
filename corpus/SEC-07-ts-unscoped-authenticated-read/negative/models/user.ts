import { DataTypes, Model } from 'sequelize'
export class UserModel extends Model {}
UserModel.init({ email: { type: DataTypes.STRING }, password: { type: DataTypes.STRING }, totpSecret: { type: DataTypes.STRING } }, { modelName: 'User' })

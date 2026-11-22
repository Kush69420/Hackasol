import { Model, DataTypes } from 'sequelize'
class UserModel extends Model {}
UserModel.init({email: {type: DataTypes.STRING}}, {modelName: 'User'})

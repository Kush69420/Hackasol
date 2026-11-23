import { DataTypes, Model } from 'sequelize'
export class OrderModel extends Model {}
OrderModel.init({ email: { type: DataTypes.STRING }, lookupCode: { type: DataTypes.STRING } }, { modelName: 'Order' })

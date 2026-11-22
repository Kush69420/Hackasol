import { DataTypes, Model } from 'sequelize'
export class MemoryModel extends Model {}
MemoryModel.init({ caption: { type: DataTypes.STRING } }, { modelName: 'Memory' })

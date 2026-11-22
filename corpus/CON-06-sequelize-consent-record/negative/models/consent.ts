import { Model, DataTypes } from 'sequelize'
class Consent extends Model {}
Consent.init({ granted: { type: DataTypes.BOOLEAN }, purpose: { type: DataTypes.STRING }, noticeVersion: { type: DataTypes.STRING }, grantedAt: { type: DataTypes.DATE } }, { sequelize })

import { Model, DataTypes } from 'sequelize'
class Consent extends Model {}
Consent.init({ granted: { type: DataTypes.BOOLEAN } }, { sequelize })

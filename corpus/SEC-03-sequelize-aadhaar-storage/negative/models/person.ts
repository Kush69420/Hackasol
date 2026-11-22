import { Model, DataTypes } from 'sequelize'
class Person extends Model {}
Person.init({ aadhaar: { type: DataTypes.STRING, set(value) { this.setDataValue('aadhaar', vault(value)) } } }, { sequelize })

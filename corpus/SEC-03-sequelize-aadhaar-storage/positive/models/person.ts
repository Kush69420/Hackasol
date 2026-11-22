import { Model, DataTypes } from 'sequelize'
class Person extends Model {}
Person.init({ aadhaar: { type: DataTypes.STRING } }, { sequelize })

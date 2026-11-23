import { Model, DataTypes } from 'sequelize'
class Customer extends Model {}
Customer.init({ email: { type: DataTypes.STRING } }, { tableName: 'Customers', paranoid: true, sequelize })

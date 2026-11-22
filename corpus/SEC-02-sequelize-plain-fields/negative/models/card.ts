import { Model, DataTypes } from 'sequelize'
class Card extends Model {}
Card.init({ cardNum: { type: DataTypes.STRING, set(value) { this.setDataValue('cardNum', encrypt(value)) } } }, { sequelize })

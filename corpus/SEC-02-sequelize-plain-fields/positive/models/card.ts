import { Model, DataTypes } from 'sequelize'
class Card extends Model {}
Card.init({ cardNum: { type: DataTypes.INTEGER } }, { sequelize })

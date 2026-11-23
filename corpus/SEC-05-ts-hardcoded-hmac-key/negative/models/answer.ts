SecurityAnswer.init({ answer: { type: DataTypes.STRING, set (answer: string) { this.setDataValue('answer', digest(answer)) } } }, { sequelize })
const digest = (value: string) => crypto.createHmac('sha256', process.env.ANSWER_KEY as string).update(value).digest('hex')

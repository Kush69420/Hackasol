User.init({ password: { type: DataTypes.STRING } }, { sequelize })
const signingKey = process.env.SIGNING_KEY
export const authorize = (account: object) => jwt.sign(account, signingKey)

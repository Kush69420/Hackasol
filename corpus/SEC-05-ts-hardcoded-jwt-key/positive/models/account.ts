User.init({ password: { type: DataTypes.STRING } }, { sequelize })
const signingKey = 'fixture-signing-material'
export const authorize = (account: object) => jwt.sign(account, signingKey)

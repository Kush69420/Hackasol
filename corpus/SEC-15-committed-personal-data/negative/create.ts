async function createAccounts() { const accounts = loadAccounts(); await Account.bulkCreate(accounts) }

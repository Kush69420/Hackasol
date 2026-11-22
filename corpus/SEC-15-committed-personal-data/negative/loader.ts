import path from 'node:path'
function loadStaticData(file: string) { return path.resolve('./data/static/' + file + '.yml') }
function loadAccounts() { return loadStaticData('accounts') }

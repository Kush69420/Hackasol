import crypto from 'node:crypto'
export const hash = (value: string) => crypto.createHash('md5').update(value).digest('hex')

import crypto from 'node:crypto'
export const etag = (value: string) => crypto.createHash('md5').update(value).digest('hex')

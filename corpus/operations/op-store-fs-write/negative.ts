import fs from 'fs'

export function readProfile (path: string) {
  if (fs.existsSync(path)) {
    return fs.readFileSync(path, 'utf8')
  }
  return ''
}

import fs from 'fs'

export function exportProfile (user: any) {
  fs.writeFileSync('/tmp/profile.json', JSON.stringify({ email: user.email }))
}

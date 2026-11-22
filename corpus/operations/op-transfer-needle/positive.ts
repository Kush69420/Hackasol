import needle from 'needle'

export function notifyCrm (user: any) {
  return needle.post('https://crm.example.com/contacts', { email: user.email }, {})
}

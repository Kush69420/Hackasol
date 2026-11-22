import needle from 'needle'

export function crmStatus () {
  return needle.get('https://crm.example.com/status')
}

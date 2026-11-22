import axios from 'axios'

export async function notifyCrm (user: any) {
  await axios.post('https://crm.example.com/contacts', { email: user.email })
}

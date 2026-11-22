import axios from 'axios'

export async function crmStatus () {
  return await axios.get('https://crm.example.com/status')
}

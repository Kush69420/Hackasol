import axios from 'axios'
export function send(user: { email: string }) { return axios.post('https://processor.example.com/contacts', { email: user.email }) }

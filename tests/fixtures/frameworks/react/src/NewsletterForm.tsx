import { useState } from 'react'
import axios from 'axios'

export function NewsletterForm() {
  const [email, setEmail] = useState('')
  const submit = () => axios.post('/api/leads', { email })
  return (
    <form onSubmit={submit}>
      <input name="email" value={email} onChange={e => setEmail(e.target.value)} />
    </form>
  )
}

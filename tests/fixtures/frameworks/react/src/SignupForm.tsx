import { useState } from 'react'

export function SignupForm() {
  const [email, setEmail] = useState('')
  const [phone, setPhone] = useState('')
  const submit = () => fetch('/api/users', { method: 'POST', body: JSON.stringify({ email, phone }) })
  return (
    <form onSubmit={submit}>
      <input name="email" value={email} onChange={e => setEmail(e.target.value)} />
      <input name="phone" value={phone} onChange={e => setPhone(e.target.value)} />
    </form>
  )
}

import { useState } from 'react'

export function WrongMethodForm() {
  const [email, setEmail] = useState('')
  const submit = () => fetch('/api/users', { method: 'PUT', body: JSON.stringify({ email }) })
  return (
    <form onSubmit={submit}>
      <input name="email" value={email} onChange={e => setEmail(e.target.value)} />
    </form>
  )
}

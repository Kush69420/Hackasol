import { useState } from 'react'

export function DynamicForm({ endpoint }: { endpoint: string }) {
  const [email, setEmail] = useState('')
  const submit = () => fetch(endpoint, { method: 'POST', body: JSON.stringify({ email }) })
  return (
    <form onSubmit={submit}>
      <input name="email" value={email} onChange={e => setEmail(e.target.value)} />
    </form>
  )
}

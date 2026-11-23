export default function Page() {
  return <form><label htmlFor="email">Email address</label><input id="email" type="email" /><input name="document" type="file" /></form>
}
export async function submit(email: string) {
  localStorage.setItem('email', email)
  return fetch('/api/verify/submit/', { method: 'POST', body: email })
}

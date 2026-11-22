export async function notifyCrm (user: any) {
  await fetch('https://crm.example.com/contacts', { method: 'POST', body: JSON.stringify({ email: user.email }) })
}

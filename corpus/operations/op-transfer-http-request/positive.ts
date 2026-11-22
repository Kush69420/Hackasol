import https from 'https'

export function notifyCrm (body: string) {
  const req = https.request({ hostname: 'crm.example.com', path: '/contacts', method: 'POST' })
  req.write(body)
  req.end()
}

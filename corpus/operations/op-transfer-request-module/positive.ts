import request from 'request'

export function notifyCrm (user: any) {
  request.post({ url: 'https://crm.example.com/contacts', form: { email: user.email } })
}

import sgMail from '@sendgrid/mail'

export async function welcome (user: any) {
  await sgMail.send({ to: user.email, from: 'shop@example.com', subject: 'Welcome', text: 'Hi' })
}

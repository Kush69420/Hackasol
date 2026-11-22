export function keepEmail (user: any) {
  sessionStorage.setItem('email', user.email)
}

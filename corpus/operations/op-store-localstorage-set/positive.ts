export function remember (user: any, rememberMe: boolean) {
  if (rememberMe) {
    localStorage.setItem('email', user.email)
  }
}

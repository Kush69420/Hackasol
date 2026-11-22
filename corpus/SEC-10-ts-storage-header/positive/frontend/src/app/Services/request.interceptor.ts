class Login { login(account: any) { localStorage.setItem('email', account.email) } }
class RequestInterceptor implements HttpInterceptor {
 intercept(req: HttpRequest<any>, next: HttpHandler) {
  req = req.clone({ setHeaders: { 'X-User-Email': String(localStorage.getItem('email')) } })
  return next.handle(req)
 }
}

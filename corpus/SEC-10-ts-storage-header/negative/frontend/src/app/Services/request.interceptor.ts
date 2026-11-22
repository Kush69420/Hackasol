class Login { login(account: any) { localStorage.setItem('email', account.email) } }
class RequestInterceptor implements HttpInterceptor {
 intercept(req: HttpRequest<any>, next: HttpHandler) {
  if (req.url.startsWith(API_BASE)) req = req.clone({ setHeaders: { 'X-User-Email': String(localStorage.getItem('email')) } })
  return next.handle(req)
 }
}

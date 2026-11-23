class RequestInterceptor implements HttpInterceptor {
 intercept(req: HttpRequest<any>, next: HttpHandler) {
  req = req.clone({ setHeaders: { Authorization: 'Bearer ' + sessionStorage.getItem('token') } })
  return next.handle(req)
 }
}

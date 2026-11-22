export class RequestInterceptor implements HttpInterceptor {
  intercept(req) {
    return req.clone({ setHeaders: { Authorization: `Bearer ${localStorage.getItem('token')}` } })
  }
}

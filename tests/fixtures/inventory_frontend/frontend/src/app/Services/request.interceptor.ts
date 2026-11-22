export class RequestInterceptor {
  intercept(req) {
    return req.clone({ setHeaders: { Authorization: `Bearer ${localStorage.getItem('token')}` } })
  }
}

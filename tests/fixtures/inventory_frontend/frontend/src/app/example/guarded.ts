export class GuardedTransport {
  intercept(request, next) {
    if (request.url.startsWith('/api/')) {
      request = request.clone({ setHeaders: { 'X-Guarded': this.headerValue } })
    }
    return next.handle(request)
  }
}
export class NotAnInterceptor {
  other(req) { return req.clone({ setHeaders: { 'X-Ignored': value } }) }
}

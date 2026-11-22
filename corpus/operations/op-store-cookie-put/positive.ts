export class BackupComponent {
  private readonly cookieService: any

  save (user: any) {
    this.cookieService.put('email', user.email, { expires: new Date() })
  }
}

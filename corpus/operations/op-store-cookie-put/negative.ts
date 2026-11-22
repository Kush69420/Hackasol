export class BackupComponent {
  private readonly cookieService: any

  read () {
    return this.cookieService.get('email')
  }
}

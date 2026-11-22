export class AccountService {
 current() { return this.http.get('/account') }
}

class AccountService { change(passwords: {password: string}) { return this.http.post('/password', passwords) } }

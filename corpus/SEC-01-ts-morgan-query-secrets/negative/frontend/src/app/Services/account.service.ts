class AccountService { change(passwords: {password: string}) { return this.http.get('/password?password=' + passwords.password) } }

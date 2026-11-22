class ExampleService {
  get(value: string) {
    return this.http.get(this.host + '/after?value=' + value)
  }
}

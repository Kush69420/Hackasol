export class ThingService {
  host = environment.hostServer + '/api/Things'
  get() { return this.http.get(this.host) }
  getById(id) { return this.http.get(`${this.host}/${id}`) }
}

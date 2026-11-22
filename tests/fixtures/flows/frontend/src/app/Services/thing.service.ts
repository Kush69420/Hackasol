export class ThingService {
  save(params) { return this.http.post('/api/Things', params) }
}

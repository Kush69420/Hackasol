@Component({ templateUrl: './example.component.html' })
export class ExampleComponent {
  service = inject(ThingService)
  emailControl = new FormControl('')
  save() {
    const payload = { email: this.emailControl.value }
    this.service.save(payload)
  }
}

@Component({ templateUrl: './example.component.html' })
export class ExampleComponent {
  model = signal({ email: '' })
  exampleForm = form(this.model)
  cardControl = new UntypedFormControl('')
  reactiveControl = new FormControl('')
}

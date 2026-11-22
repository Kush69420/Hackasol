export class ReviewsComponent {
 reviews = inject(ReviewsService)
 accounts = inject(AccountService)
 init() { this.accounts.current().subscribe((account) => { this.author.set(account.email) }) }
 submit() { const review = { author: this.author(), message: this.message }; this.reviews.create(review) }
}

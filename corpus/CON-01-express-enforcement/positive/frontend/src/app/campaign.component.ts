class CampaignComponent {
  submit() { if (this.consent) { this.http.post('/marketing', { email: this.email }) } }
}

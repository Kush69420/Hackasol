class ConsentEvent(models.Model):
    user = models.ForeignKey(User)
    action = models.CharField()
    purpose = models.CharField()
    consent_version = models.CharField()
    timestamp = models.DateTimeField(auto_now_add=True)

class GrantView(View):
    template_name = "grant.html"
    def post(self, request):
        ConsentEvent.objects.create(user=request.user, action="GRANTED", purpose="messages", consent_version="v1")

class WithdrawView(View):
    template_name = "withdraw.html"
    def post(self, request):
        withdraw_consent(request.user)

urlpatterns = [path("grant/", GrantView.as_view(), name="grant"), path("withdraw/", WithdrawView.as_view(), name="withdraw")]

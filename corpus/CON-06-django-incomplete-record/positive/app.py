class ConsentEvent(models.Model):
    user = models.ForeignKey(User)
    action = models.CharField()
    purpose = models.CharField()
    timestamp = models.DateTimeField(auto_now_add=True)

class GrantView(View):
    template_name = "grant.html"
    def post(self, request):
        ConsentEvent.objects.create(user=request.user, action="GRANTED", purpose="messages")

urlpatterns = [path("grant/", GrantView.as_view(), name="grant")]

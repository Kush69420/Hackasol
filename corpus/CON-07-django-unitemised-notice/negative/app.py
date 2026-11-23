class GrantView(View):
    template_name = "grant.html"
    def post(self, request):
        ConsentEvent.objects.create(user=request.user, action="GRANTED", purpose="messages")

urlpatterns = [path("grant/", GrantView.as_view(), name="grant")]

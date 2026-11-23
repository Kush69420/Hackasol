from django.db import models

class Record(models.Model):
    aadhaar_number = models.CharField(max_length=20)

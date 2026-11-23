from django.db import models

class Record(models.Model):
    aadhaar_number = models.EncryptedCharField(max_length=20)

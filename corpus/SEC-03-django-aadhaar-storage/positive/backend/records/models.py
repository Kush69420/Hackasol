from django.db import models

class DocumentType(models.TextChoices):
    AADHAAR = 'aadhaar', 'Aadhaar'
    PAN = 'pan', 'PAN'

class Document(models.Model):
    document_type = models.CharField(max_length=20, choices=DocumentType.choices)
    document_number = models.CharField(max_length=100)

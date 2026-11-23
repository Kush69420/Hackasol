from django.db import models

class Person(models.Model):
    email = models.EmailField()
    aadhaar_number = models.CharField(max_length=12)
    face_image = models.ImageField()
    private_note = models.TextField()

    class Meta:
        db_table = 'people_records'

class DocumentKind(models.TextChoices):
    NATIONAL = 'aadhaar', 'National ID'
    TAX = 'pan', 'Tax ID'

class Document(models.Model):
    document_type = models.CharField(max_length=20, choices=DocumentKind.choices)
    document_number = models.CharField(max_length=20)

class OtherDocument(models.Model):
    document_type = models.CharField(max_length=20, choices=[('passport', 'Passport')])
    document_number = models.CharField(max_length=20)

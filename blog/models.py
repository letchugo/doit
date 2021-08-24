
from django.db import models

class Post(models.Model):
    title = models.CharField(max_length=30)
    content = models.TextField()

    created_at = models.DateTimeField(auto_now=True)
    #자동으로 작성시각과 수정시각 저장하는것
    update_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return f'[{self.pk}]{self.title}'

# Create your models here.


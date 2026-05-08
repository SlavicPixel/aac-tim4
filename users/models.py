from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    pass

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
class Counselor(models.Model):
    """
    Savjetnik model linkan na User account.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='counselor_profile'
    )

    class Meta:
        verbose_name = 'Counselor'
        verbose_name_plural = 'Counselors'

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"

    @property
    def full_name(self):
        return f"{self.user.first_name} {self.user.last_name}"

    @property
    def email(self):
        return self.user.email
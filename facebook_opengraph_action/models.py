from django.db import models


class OpenGraphActionModel(models.Model):
    user = models.ForeignKey('auth.User')
    facebook_action_id = models.BigIntegerField(blank=True, null=True)
    executed = models.BooleanField(blank=True)
    executed_at = models.DateTimeField(auto_now_add=True)
    error_code = models.IntegerField(blank=True, null=True)

    class Meta:
        abstract = True
        unique_together = (
            ('content', 'user',),
        )

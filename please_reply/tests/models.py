from django.db import models
from django.template.defaultfilters import slugify

class Event(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=512)

    def save(self):
        """
        populate the slugfield.

        """
        if not self.slug:
            self.slug = slugify(self.title)

        super(Event, self).save()


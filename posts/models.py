from django.contrib.auth import get_user_model
from django.db import models
from django.contrib.auth.hashers import make_password, check_password

User = get_user_model()


class Journal(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True,)
    pub_date = models.DateTimeField('Дата публикации', auto_now_add=True)
    last_modified = models.DateTimeField('Дата обновления', auto_now=True)
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='journals')
    image = models.ImageField(
        upload_to='posts/', null=True, blank=True, default=None)
    is_private = models.BooleanField(
        default=False,
        verbose_name="Приватный пост",
        help_text="Если отмечено, журнал доступен только автору"
    )
    pin_code = models.CharField(
        max_length=128,
        null=True,
        blank=True,
        default=None,
        verbose_name="Защитный PIN-код",
        help_text="Необязательный код для доступа к посту (4-6 цифр)"
    )

    def save(self, *args, **kwargs):
        if self.pk:
            previous = Journal.objects.get(pk=self.pk)
            if previous.is_private != self.is_private:
                if not self.is_private:
                    self.posts.update(is_private=False)
                else:
                    self.posts.update(is_private=True)
        if not self.is_private:
            self.pin_code = None

        super(Journal, self).save(*args, **kwargs)

    def set_pin(self, raw_pin):
        if raw_pin:
            self.pin_code = make_password(raw_pin)
        else:
            self.pin_code = None

    def check_pin(self, raw_pin):
        if not self.pin_code:
            return True
        return check_password(raw_pin, self.pin_code)

    class Meta:
        ordering = ['-last_modified', 'title']

    def __str__(self):
        return self.title


class Post(models.Model):
    text = models.TextField()
    pub_date = models.DateTimeField('Дата публикации', auto_now_add=True)
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='posts')
    image = models.ImageField(
        upload_to='posts/', null=True, blank=True, default=None)
    is_private = models.BooleanField(
        default=False,
        verbose_name="Приватный пост",
        help_text="Если отмечено, пост доступен только автору"
    )
    journal = models.ForeignKey(Journal, on_delete=models.CASCADE,
                                related_name='posts')

    def save(self, *args, **kwargs):
        if self.journal.is_private:
            self.is_private = True

        super(Post, self).save(*args, **kwargs)

    class Meta:
        ordering = ['-pub_date', 'text']

    def __str__(self):
        return self.text


class Follow(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='following')
    following = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='followers')

    class Meta:
        unique_together = ('user', 'following')

    def __str__(self):
        return f'{self.user.username} follows {self.following.username}'

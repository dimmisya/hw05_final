from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

User = get_user_model()


class PostCreateFormTests(TestCase):
    def test_create_post(self):
        """Проверка формы регистрации."""
        users_count = User.objects.count()
        form_data = {
            'first_name': 'Дмитрий',
            'last_name': 'Менделеев',
            'username': 'mendim',
            'email': 'mendim@mail.com',
            'password1': 'Pass123_word',
            'password2': 'Pass123_word',
        }
        response = self.client.post(
            reverse('users:signup'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
                             'posts:index'))
        self.assertEqual(User.objects.count(), users_count + 1,
                         'Проверьте, что пользователь сохранен в базе')
        self.assertTrue(
            User.objects.filter(
                username='mendim',).exists()
        )

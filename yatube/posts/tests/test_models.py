from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост для проверки',
        )

    def test_models_have_correct_object_names(self):
        """Проверка представления моделей."""
        post = PostModelTest.post
        group = PostModelTest.group
        str_text = {
            'Тестовый пост д': post,
            'Тестовая группа': group,
        }
        for field, expected_value in str_text.items():
            with self.subTest(field=expected_value):
                self.assertEqual(
                    field, str(expected_value))

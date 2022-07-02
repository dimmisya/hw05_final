from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase

from ..models import Group, Post

User = get_user_model()


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='auth')
        cls.user = User.objects.create_user(username='HasNoName')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='foto',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост для проверки',
            group=cls.group
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_author = Client()
        self.authorized_client.force_login(StaticURLTests.user)
        self.authorized_author.force_login(StaticURLTests.author)
        self.slug = StaticURLTests.post.group.slug
        self.username = StaticURLTests.post.author.username
        self.post_id = StaticURLTests.post.pk
        self.templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{self.slug}/': 'posts/group_list.html',
            f'/profile/{self.username}/': 'posts/profile.html',
            f'/posts/{self.post_id}/': 'posts/post_detail.html',
            f'/posts/{self.post_id}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
        }
        cache.clear()

    def test_urls_uses_correct_template(self):
        """URLs используют верный шаблон."""
        for address, template in self.templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_author.get(address)

                self.assertTemplateUsed(response, template)

    def test_urls_exists_at_desired_location(self):
        """Страницы доступны по URLs."""
        for address in self.templates_url_names:
            with self.subTest(address=address):
                response = self.authorized_author.get(address)

                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_edit_only_for_author(self):
        """Редактирование поста доступно только автору"""
        response = self.authorized_client.get(f'/posts/{self.post_id}/edit/')

        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_post_create_only_for_authorized_client(self):
        """Создание поста доступно только авторизованному клиенту."""
        response = self.guest_client.get('/create/')

        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_nonexist_page_unavailable(self):
        """Несуществующий адрес - недоступен."""
        response = self.guest_client.get('/unexisting_page/')

        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

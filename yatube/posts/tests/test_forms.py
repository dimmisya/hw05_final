import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.shortcuts import get_object_or_404
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='foto',
            description='Тестовое описание',
        )
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_author = Client()
        self.authorized_author.force_login(PostCreateFormTests.author)

    def test_create_post(self):
        """Проверка формы создания поста."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый текст',
            'image': PostCreateFormTests.uploaded,
        }
        response = self.authorized_author.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': 'auth'}))
        self.assertEqual(Post.objects.count(), posts_count + 1,
                         'Проверьте, что пост сохранен в базе')
        self.assertTrue(
            Post.objects.filter(
                text='Тестовый текст',
                image='posts/small.gif').exists())

    def test_edit_post(self):
        """Проверка формы редактирования поста."""
        Post.objects.create(
            author=PostCreateFormTests.author,
            text='Тестовый пост для проверки',
        )
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Проверка редактирования',
        }
        response = self.authorized_author.post(
            reverse('posts:post_edit', kwargs={'post_id': 1}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'post_id': 1}))
        self.assertEqual(Post.objects.count(), posts_count,
                         'Проверьте, что не создается новый пост')
        self.assertTrue(
            Post.objects.filter(
                pk=1,
                text='Проверка редактирования',).exists()
        )

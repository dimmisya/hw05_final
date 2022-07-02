import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Comment, Follow, Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
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
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост для проверки',
            group=cls.group,
            image=cls.uploaded
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_author = Client()
        self.authorized_author.force_login(PostPagesTests.author)
        self.reverse_index = reverse('posts:index')
        self.reverse_group = reverse('posts:group', kwargs={'slug': 'foto'})
        self.reverse_profile = reverse('posts:profile',
                                       kwargs={'username': 'auth'})
        self.reverse_post_detail = reverse('posts:post_detail',
                                           kwargs={'post_id': 1})
        self.post_edit = reverse('posts:post_edit', kwargs={'post_id': 1})
        self.post_create = reverse('posts:post_create')
        cache.clear()

    def test_pages_uses_correct_template(self):
        """Страницы использует соответствующий шаблон."""
        templates_pages_names = {
            self.reverse_index: 'posts/index.html',
            self.reverse_group:
            'posts/group_list.html',
            self.reverse_profile:
            'posts/profile.html',
            self.reverse_post_detail:
            'posts/post_detail.html',
            self.post_edit:
            'posts/create_post.html',
            self.post_create: 'posts/create_post.html',
        }

        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_author.get(reverse_name)

                self.assertTemplateUsed(response, template)

    def test_list_pages_show_correct_context(self):
        """Шаблон страниц-списков сформирован с правильным контекстом."""
        reverse_names = (self.reverse_index,
                         self.reverse_group,
                         self.reverse_profile, )

        for reverse_name in reverse_names:
            response = self.authorized_author.get(reverse_name)
            first_object = response.context['page_obj'][0]
            context = {'auth': first_object.author.username,
                       'Тестовый пост для проверки': first_object.text,
                       'Тестовая группа': first_object.group.title,
                       'posts/small.gif': first_object.image.name,
                       }
            for expected_context, test_context in context.items():
                with self.subTest(expected_context=expected_context):

                    self.assertEqual(expected_context, test_context)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон страницы поста сформирован с правильным контекстом."""
        response = self.authorized_author.get(self.reverse_post_detail)
        object = response.context['post']
        context = {'auth': object.author.username,
                   'Тестовый пост для проверки': object.text,
                   'Тестовая группа': object.group.title,
                   1: object.pk,
                   'posts/small.gif': object.image.name,
                   }

        for expected_context, test_context in context.items():
            with self.subTest(expected_context=expected_context):

                self.assertEqual(expected_context, test_context)

    def test_post_form_pages_show_correct_context(self):
        """Проверка, что поля форм имеют ожидаемый тип."""
        reverse_names = (self.post_create,
                         self.post_edit, )

        for reverse_name in reverse_names:
            response = self.authorized_author.get(reverse_name)
            form_fields = {
                'text': forms.fields.CharField,
                'group': forms.fields.ChoiceField,
                'image': forms.fields.ImageField,
            }
            for value, expected in form_fields.items():
                with self.subTest(value=value):
                    form_field = response.context.get('form').fields.get(value)

                    self.assertIsInstance(form_field, expected)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='foto',
            description='Тестовое описание',
        )
        cls.reverse_names = (reverse('posts:index'),
                             reverse('posts:group', kwargs={'slug': 'foto'}),
                             reverse('posts:profile',
                                     kwargs={'username': 'auth'}), )
        cls.posts_count = 13
        for i in range(cls.posts_count):
            Post.objects.create(
                author=cls.author,
                text=f'Тестовый пост {i} для проверки',
                group=cls.group
            )
        cache.clear()

    def test_first_page_contains_ten_records(self):
        """Проверка кол-ва записей на 1-й странице."""
        for reverse_name in PaginatorViewsTest.reverse_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.client.get(reverse_name)
                self.assertEqual(len(response.context['page_obj']),
                                 settings.POSTS_PER_PAGE)

    def test_second_page_contains_three_records(self):
        """Проверка кол-ва записей на 2-й странице."""
        for reverse_name in PaginatorViewsTest.reverse_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.client.get(reverse_name + '?page=2')
                self.assertEqual(len(response.context['page_obj']),
                                 PaginatorViewsTest.posts_count
                                 - settings.POSTS_PER_PAGE)


class PostCreateViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='auth')
        cls.group_foto = Group.objects.create(
            title='Тестовая группа Фото',
            slug='foto',
            description='Тестовое описание',
        )
        cls.group_lyrics = Group.objects.create(
            title='Тестовая группа Стихи',
            slug='lyrics',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост для проверки',
            group=cls.group_foto
        )

    def test_list_pages_contains_post(self):
        """Проверка, что пост попал на нужные страницы"""
        pages_posts_count = {
            reverse('posts:index'): 1,
            reverse('posts:group', kwargs={'slug': 'foto'}): 1,
            reverse('posts:group', kwargs={'slug': 'lyrics'}): 0,
            reverse('posts:profile', kwargs={'username': 'auth'}): 1,
        }
        cache.clear()
        for reverse_name, count in pages_posts_count.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.client.get(reverse_name)
                self.assertEqual(len(response.context['page_obj']), count)


class CommentCreateViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='auth')
        cls.post_1 = Post.objects.create(
            author=cls.author,
            text='Тестовый пост для проверки 1',
        )
        cls.post_2 = Post.objects.create(
            author=cls.author,
            text='Тестовый пост для проверки 2',
        )
        cls.comment = Comment.objects.create(
            author=cls.author,
            text='Тестовый коммент для проверки',
            post=cls.post_1,
        )

    def test_post_page_contains_comment(self):
        """Проверка, что комментарий попал на нужные страницы"""
        pages_comments_count = {
            reverse('posts:post_detail', kwargs={'post_id': 1}): 1,
            reverse('posts:post_detail', kwargs={'post_id': 2}): 0,
        }
        for reverse_name, count in pages_comments_count.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.client.get(reverse_name)
                self.assertEqual(len(response.context['comments']), count)


class CacheViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='auth')
        cls.group_foto = Group.objects.create(
            title='Тестовая группа Фото',
            slug='foto',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост для проверки',
            group=cls.group_foto
        )
        cache.clear()

    def test_index_page_cache(self):
        """Проверка работы кэша главной страницы"""
        response = self.client.get(reverse('posts:index'))
        page_content = response.content
        self.assertEqual(page_content, response.content)
        CacheViewsTest.post.delete()
        response = self.client.get(reverse('posts:index'))
        self.assertEqual(page_content, response.content)
        cache.clear()
        response = self.client.get(reverse('posts:index'))
        self.assertNotEqual(page_content, response.content)


class FollowCreateViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='auth')
        cls.follower = User.objects.create_user(username='follower')
        cls.user = User.objects.create_user(username='user')
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост для проверки',
        )

    def setUp(self):
        self.authorized_follower = Client()
        self.authorized_user = Client()
        self.authorized_follower.force_login(FollowCreateViewsTest.follower)
        self.authorized_user.force_login(FollowCreateViewsTest.user)
        cache.clear()

    def test_follow_unfollow_work(self):
        """Проверка создания и удаления подписки """
        reverse_names = {
            reverse('posts:profile_follow', kwargs={'username': 'auth'}): 1,
            reverse('posts:profile_unfollow', kwargs={'username': 'auth'}): 0,
        }
        for reverse_name, count in reverse_names.items():
            with self.subTest(reverse_name=reverse_name):
                self.authorized_user.get(reverse_name)
                self.assertEqual(len(Follow.objects.all()), count)

    def test_follower_list_pages_contains_post(self):
        """Проверка, что пост попал на нужные страницы подписчика"""
        Follow.objects.create(
            author=FollowCreateViewsTest.author,
            user=FollowCreateViewsTest.follower,
        )
        pages_posts_count = {
            reverse('posts:index'): 1,
            reverse('posts:follow_index'): 1,
        }
        for reverse_name, count in pages_posts_count.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_follower.get(reverse_name)
                self.assertEqual(len(response.context['page_obj']), count)

    def test_user_list_pages_contains_post(self):
        """Проверка, что пост не попал страницу не подписанного пользователя"""
        Follow.objects.create(
            author=FollowCreateViewsTest.author,
            user=FollowCreateViewsTest.follower,
        )
        pages_posts_count = {
            reverse('posts:index'): 1,
            reverse('posts:follow_index'): 0,
        }
        for reverse_name, count in pages_posts_count.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_user.get(reverse_name)
                self.assertEqual(len(response.context['page_obj']), count)

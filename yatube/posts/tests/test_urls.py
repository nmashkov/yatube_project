from http import HTTPStatus

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.core.cache import cache

from posts.models import Post, Group

User = get_user_model()


class TaskURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='TestPostAuthor')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.get(username='TestPostAuthor')
        self.auth_author = Client()
        self.auth_author.force_login(self.user)
        cache.clear()

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            '/create/': 'posts/post_create.html',
            f'/posts/{self.post.pk}/': 'posts/post_detail.html',
            f'/posts/{self.post.pk}/edit/': 'posts/post_create.html',
            f'/profile/{self.user.username}/': 'posts/profile.html',
            '/follow/': 'posts/follow.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.auth_author.get(address)
                self.assertTemplateUsed(response, template)

    def test_unexpected_url_give_404(self):
        """Проверка ошибки 404 на несуществующую страницу."""
        response = self.guest_client.get('/some_unexpected_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_urls_access_for_guest(self):
        """Проверка доступности страниц для гостя сайта."""
        page_status = {
            '/': HTTPStatus.OK,
            f'/group/{self.group.slug}/': HTTPStatus.OK,
            '/create/': HTTPStatus.FOUND,
            f'/posts/{self.post.pk}/': HTTPStatus.OK,
            f'/posts/{self.post.pk}/edit/': HTTPStatus.FOUND,
            f'/posts/{self.post.pk}/comment/': HTTPStatus.FOUND,
            f'/profile/{self.user.username}/': HTTPStatus.OK,
            f'/profile/{self.user.username}/follow/': HTTPStatus.FOUND,
            f'/profile/{self.user.username}/unfollow/': HTTPStatus.FOUND,
            '/follow/': HTTPStatus.FOUND,
        }
        for address, status in page_status.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, status)

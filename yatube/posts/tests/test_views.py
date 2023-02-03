from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.test import Client, TestCase
from django.urls import reverse
from django import forms
from django.core.cache import cache

from posts.models import Post, Group

User = get_user_model()


class TaskViewTests(TestCase):
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
            text='Тестовая запись',
            group=cls.group,
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.get(username='TestPostAuthor')
        self.auth_author = Client()
        self.auth_author.force_login(self.user)
        self.auth_user = User.objects.create(username='TestAuthClient')
        self.auth_client = Client()
        self.auth_client.force_login(self.auth_user)
        self.post_list = self.user.posts.all()
        self.post_count = self.post_list.count()
        cache.clear()

    def test_cache_index_page(self):
        """Проверка кеширования главной страницы."""
        test_post = Post.objects.create(
            author=self.user,
            text='Тестовая запись 2',
            group=self.group,
        )
        post_count = Post.objects.count()
        response = self.guest_client.get(reverse('posts:index'))
        page_obj = response.context.get('page_obj')
        test_post.delete()
        self.assertEqual(len(page_obj), post_count)
        cache.clear()
        self.assertEqual(Post.objects.count(), post_count - 1)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        page_names_templates = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list', kwargs={'slug': 'test-slug'}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile', kwargs={'username': self.user.username}
            ): 'posts/profile.html',
            reverse('posts:follow_index'): 'posts/follow.html',
            reverse(
                'posts:post_detail', kwargs={'post_id': self.post.pk}
            ): 'posts/post_detail.html',
            reverse(
                'posts:post_edit', kwargs={'post_id': self.post.pk}
            ): 'posts/post_create.html',
        }
        for reverse_name, template in page_names_templates.items():
            with self.subTest(template=template):
                response = self.auth_author.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        post_list = Post.objects.all()
        paginator = Paginator(post_list, 10)
        page_obj = paginator.get_page(1)
        response = (self.guest_client.get(reverse('posts:index')))
        self.assertEqual(
            response.context.get('title'), 'Последние обновления на сайте')
        self.assertEqual(
            response.context.get('page_obj').object_list[0],
            page_obj.object_list[0])

    def test_group_page_show_correct_context(self):
        """Шаблон group_posts сформирован с правильным контекстом."""
        group_posts = self.group.group_posts.all()
        paginator = Paginator(group_posts, 10)
        page_obj = paginator.get_page(1)
        response = (self.guest_client.get(
            reverse('posts:group_list', kwargs={'slug': 'test-slug'})
        ))
        self.assertEqual(
            response.context.get('group'), self.group)
        self.assertEqual(
            response.context.get('title'),
            f'Записи сообщества {str(self.group)}')
        self.assertEqual(
            response.context.get('page_obj').object_list[0],
            page_obj.object_list[0])

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        paginator = Paginator(self.post_list, 10)
        page_obj = paginator.get_page(1)
        response = (self.guest_client.get(
            reverse('posts:profile', kwargs={'username': self.user.username})
        ))
        self.assertEqual(
            response.context.get('author'), self.user)
        self.assertEqual(
            response.context.get('title'),
            f'Профайл пользователя {self.user.username}')
        self.assertEqual(
            response.context.get('count'), self.post_count)
        self.assertEqual(
            response.context.get('page_obj').object_list[0],
            page_obj.object_list[0])

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = (self.guest_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.pk})
        ))
        self.assertEqual(
            response.context.get('title'), 'Пост: Тестовая запись')
        self.assertEqual(
            response.context.get('count'), self.post_list.count())
        self.assertEqual(
            response.context.get('post'), self.post)
        self.assertEqual(
            response.context.get('comments').count(),
            self.post.comments.count())

    def test_edit_form_correct_fields(self):
        """Проверка формы редактирования записи на странице post_create."""
        response = self.auth_author.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk}))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_create_form_correct_fields(self):
        """Проверка формы создания записи на странице post_create."""
        response = self.auth_author.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_new_post_with_group_exits_on_pages(self):
        """Проверка наличия новой записи второй группы на всех страницах."""
        group_2 = Group.objects.create(
            title='Тестовая группа 2',
            slug='test-slug-2',
            description='Тестовое описание 2',
        )
        new_post_group_2 = Post.objects.create(
            author=self.user,
            text='Тестовая запись 2',
            group=group_2,
        )
        response_index = self.guest_client.get(reverse('posts:index'))
        self.assertTrue(
            new_post_group_2 in response_index.context.get('page_obj'))
        response_group_1 = self.guest_client.get(
            reverse('posts:group_list', kwargs={'slug': 'test-slug'}))
        self.assertTrue(
            new_post_group_2 not in response_group_1.context.get('page_obj'))
        response_group_2 = self.guest_client.get(
            reverse('posts:group_list', kwargs={'slug': 'test-slug-2'}))
        self.assertTrue(
            new_post_group_2 in response_group_2.context.get('page_obj'))
        response_profile = self.guest_client.get(
            reverse('posts:profile', kwargs={'username': self.user}))
        self.assertTrue(
            new_post_group_2 in response_profile.context.get('page_obj'))

    def test_auth_client_follow(self):
        """Проверка работы подписки на автора."""
        author = self.post.author
        followers = author.following.count()
        response = (self.auth_client.post(
            reverse('posts:profile_follow', kwargs={'username': author})
        ))
        self.assertEqual(author.following.count(), followers + 1)
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': author}))

    def test_auth_client_unfollow(self):
        """Проверка работы отписки от автора."""
        author = self.post.author
        response = (self.auth_client.post(
            reverse('posts:profile_follow', kwargs={'username': author})
        ))
        followers = author.following.count()
        response = (self.auth_client.post(
            reverse('posts:profile_unfollow', kwargs={'username': author})
        ))
        self.assertEqual(author.following.count(), followers - 1)
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': author}))

    def test_following_client_follow_page_content(self):
        """Проверка списка постов на странице подписок клиента."""
        author = self.post.author
        response = (self.auth_client.post(
            reverse('posts:profile_follow', kwargs={'username': author})
        ))
        response = self.auth_client.get(reverse('posts:follow_index'))
        self.assertEqual(len(response.context['page_obj']), 1)

    def test_unfollowing_client_follow_page_content(self):
        """Проверка списка постов на странице подписок клиента."""
        response = self.auth_author.get(reverse('posts:follow_index'))
        self.assertEqual(
            response.context['title'],
            'У вас ещё нет подписок'
        )


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='TestPostAuthor')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.posts = []
        for i in range(11):
            cls.posts.append(Post.objects.create(
                author=cls.user,
                text='Тестовая запись',
                group=cls.group,
            ))

    def setUp(self):
        self.guest_client = Client()

    def test_index_first_page_contains_ten_records(self):
        """Проверка количества записей на главной странице (1стр)."""
        response = self.guest_client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_index_second_page_contains_one_records(self):
        """Проверка количества записей на главной странице (2стр)."""
        response = self.guest_client.get(reverse('posts:index') + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 1)

    def test_group_first_page_contains_ten_records(self):
        """Проверка количества записей на странице группы (1стр)."""
        response = self.guest_client.get(
            reverse('posts:group_list', kwargs={'slug': 'test-slug'}))
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_group_second_page_contains_ten_records(self):
        """Проверка количества записей на странице группы (2стр)."""
        response = self.guest_client.get(
            reverse(
                'posts:group_list', kwargs={'slug': 'test-slug'}) + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 1)

    def test_profile_first_page_contains_ten_records(self):
        """Проверка количества записей на странице профиля (1стр)."""
        response = self.guest_client.get(
            reverse('posts:profile', kwargs={'username': self.user.username}))
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_profile_second_page_contains_ten_records(self):
        """Проверка количества записей на странице профиля (2стр)."""
        response = self.guest_client.get(
            reverse(
                'posts:profile', kwargs={'username': self.user.username}
            ) + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 1)

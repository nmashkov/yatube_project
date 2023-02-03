import shutil
import tempfile
# import unittest
from http import HTTPStatus

from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model

from posts.models import Post, Group

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class TaskCreateFormTests(TestCase):
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

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.auth_user = User.objects.create(username='AuthClient')
        self.auth_client = Client()
        self.auth_client.force_login(self.auth_user)

    # @unittest.skip
    def test_create_new_comment(self):
        """Валидная форма создает новый комментарий под записью."""
        comments = self.post.comments.all()
        comments_count = comments.count()
        test_text = 'Тестовый комментарий'
        form_data = {
            'text': test_text,
        }
        response = self.auth_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': self.post.pk}),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'post_id': self.post.pk}))
        self.assertEqual(comments.count(), comments_count + 1)
        self.assertTrue(
            comments.filter(
                text=test_text,
                post=self.post,
                author=self.auth_user,
            ).exists()
        )

    # @unittest.skip
    def test_create_new_post(self):
        """Валидная форма создает новую запись на сайте."""
        posts_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        test_text = 'Тестовый текст новой записи'
        selected_group = self.group.id
        form_data = {
            'text': test_text,
            'group': selected_group,
            'image': uploaded,
        }
        response = self.auth_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(response, reverse(
            'posts:profile', args=[self.auth_user]))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text=test_text,
                group=selected_group,
            ).exists()
        )

    def test_create_new_post_with_wrong_file_instead_image(self):
        """
        Проверка формы создания записи, если пользователь загрузит
        не картинку.
        """
        test_text = 'Тестовый текст новой записи'
        selected_group = self.group.id
        # wrong_file = tempfile.NamedTemporaryFile(suffix=".gif").name
        wrong_file1 = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        wrong_file = SimpleUploadedFile(
            name='wrong_file.mp4',
            content=wrong_file1,
            content_type='video/mp4'
        )
        form_data = {
            'text': test_text,
            'group': selected_group,
            'image': wrong_file,
        }
        response = self.auth_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Post.objects.filter(
            image__contains='wrong_file.mp4').exists(), False)

    # @unittest.skip
    def test_edit_post(self):
        """Проверка работы формы редактирования существующей записи."""
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        new_post = Post.objects.create(
            author=self.auth_user,
            text='Тестовый пост 1',
            group=self.group,
            image=uploaded,
        )
        group_2 = Group.objects.create(
            title='Тестовая группа 2',
            slug='test-slug-2',
            description='Тестовое описание 2',
        )
        posts_count = Post.objects.count()
        response = self.auth_client.get(
            reverse('posts:post_edit', kwargs={'post_id': new_post.pk})
        )
        form = response.context['form']
        form_data = form.initial
        form_data['text'] = 'Тестовый пост 1 ИЗМЕНЁННЫЙ'
        form_data['group'] = group_2.id
        response = self.auth_client.post(
            reverse('posts:post_edit', kwargs={
                'post_id': new_post.pk
            }),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'post_id': new_post.pk}))
        self.assertTrue(
            Post.objects.filter(
                text='Тестовый пост 1 ИЗМЕНЁННЫЙ',
                group=group_2,
            ).exists()
        )
        self.assertEqual(response.status_code, 200)

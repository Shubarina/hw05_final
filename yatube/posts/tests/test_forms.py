import shutil
import tempfile

from http import HTTPStatus

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.forms import PostForm
from posts.models import Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

CREATE = 'posts:post_create'
PROFILE = 'posts:profile'
EDIT = 'posts:post_edit'


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание'
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый текст',
            group=cls.group
        )
        cls.form = PostForm()
        cls.user = User.objects.create_user(username='Anna')
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
    def tearDownClass(cls) -> None:
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_author = Client()
        self.authorized_author.force_login(PostFormTests.post.author)

    def test_post_create(self):
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый второй текст',
            'group': self.group.id,
            'image': self.uploaded,
        }
        response = self.authorized_client.post(
            reverse(CREATE),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(response, reverse(
            PROFILE, kwargs={'username': self.user.username}))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        new_post = Post.objects.latest('pub_date')
        self.assertEqual(new_post.text, form_data['text'])
        self.assertEqual(new_post.group.id, form_data['group'])
        self.assertEqual(new_post.author.username, self.user.username)
        self.assertTrue(
            Post.objects.filter(
                image='posts/{}'.format(form_data['image'].name)
            ).exists
        )

    def test_post_edit(self):
        posts_count = Post.objects.count()
        form_changes = {
            'text': 'Редакция поста',
            'group': self.group.id,
        }
        response = self.authorized_author.post(
            reverse(EDIT, kwargs={
                'post_id': PostFormTests.post.id}),
            data=form_changes,
            follow=True,
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        edited_post = Post.objects.all().last()
        self.assertEqual(edited_post.text, form_changes['text'])
        self.assertEqual(edited_post.group.id, form_changes['group'])
        self.assertEqual(
            edited_post.author.username, self.author.username
        )

from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post, User

INDEX = 'posts:index'
GROUP = 'posts:group_list'
DETAIL = 'posts:post_detail'
CREATE = 'posts:post_create'
PROFILE = 'posts:profile'
EDIT = 'posts:post_edit'
COMMENT = 'posts:add_comment'


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост',
        )
        cls.user = User.objects.create_user(username='NotAuthor')

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_author = Client()
        self.authorized_author.force_login(self.author)

    def test_urls_uses_correct_template(self):
        templates_url_names = {
            'posts/index.html': reverse(INDEX),
            'posts/group_list.html': reverse(
                GROUP, kwargs={'slug': self.group.slug}
            ),
            'posts/profile.html': reverse(
                PROFILE, kwargs={'username': self.user.username}
            ),
            'posts/post_detail.html': reverse(
                DETAIL, kwargs={'post_id': self.post.id}
            ),
            'posts/create_post.html': reverse(CREATE),
            'posts/edit_post.html': reverse(
                EDIT, kwargs={'post_id': self.post.id}
            ),
            'core/404csrf.html': '/unexisting_page/',
        }
        for template, address in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_author.get(address)
                self.assertTemplateUsed(response, template)

    def test_pages_status_any(self):
        pages_status_list = {
            reverse(INDEX),
            reverse(GROUP, kwargs={'slug': self.group.slug}),
            reverse(PROFILE, kwargs={'username': self.user.username}),
            reverse(DETAIL, kwargs={'post_id': self.post.id}),
        }
        for page in pages_status_list:
            with self.subTest(page):
                response = self.guest_client.get(page)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_pages_status_authorized(self):
        pages_authorized = {
            reverse(CREATE): HTTPStatus.OK,
            reverse(EDIT, kwargs={'post_id': self.post.id}): HTTPStatus.FOUND,
        }
        for page, status in pages_authorized.items():
            with self.subTest(page=page):
                response = self.authorized_client.get(page)
                self.assertEqual(response.status_code, status)

    def test_unexisting_url_access_any(self):
        """Страница доступна любому пользователю"""
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_create_url_redirect_anonymous(self):
        """Страница перенаправляет неавторизованного пользователя"""
        response = self.guest_client.get('/create/', follow=True)
        self.assertRedirects(response, '/auth/login/?next=/create/')

    def test_post_edit_url_author_access(self):
        """Страница поста доступна автору для редактирования"""
        response = self.authorized_author.get(reverse(
            DETAIL, kwargs={'post_id': self.post.id})
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_comment_url_redirect_anonymous(self):
        """Комментировать посты может только авторизованый пользователь"""
        response = self.guest_client.get(reverse(
            COMMENT, kwargs={'post_id': self.post.id})
        )
        self.assertRedirects(
            response, f'/auth/login/?next=/posts/{self.post.id}/comment/'
        )

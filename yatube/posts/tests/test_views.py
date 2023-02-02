import shutil
import tempfile

from django import forms
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Comment, Follow, Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

INDEX = 'posts:index'
GROUP = 'posts:group_list'
DETAIL = 'posts:post_detail'
CREATE = 'posts:post_create'
PROFILE = 'posts:profile'
EDIT = 'posts:post_edit'
COMMENT = 'posts:add_comment'
FOLLOW = 'posts:follow_index'


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostViewTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
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
            text='Тестовый пост',
            group=cls.group,
            image=cls.uploaded
        )
        cls.second_group = Group.objects.create(
            title='Вторая группа',
            slug='second-slug',
            description='Вторая тестовая группа'
        )
        cls.user = User.objects.create_user(username='NotAuthor')
        cls.follower = User.objects.create_user(username='Anna')

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_author = Client()
        self.authorized_author.force_login(self.author)
        self.authorized_follower = Client()
        self.authorized_follower.force_login(self.follower)

    def test_pages_paginator_posts(self):
        cache.clear()
        for post in range(12):
            Post.objects.create(
                author=self.user,
                text='посты для паджинатора',
                group=self.group,
            )
        pages_amount = {
            reverse(INDEX): 10,
            reverse(INDEX) + '?page=2': 3,
            reverse(GROUP, kwargs={
                'slug': self.group.slug}): 10,
            reverse(GROUP, kwargs={
                'slug': self.group.slug}) + '?page=2': 3,
            reverse(PROFILE, kwargs={
                'username': self.user.username}): 10,
            reverse(PROFILE, kwargs={
                'username': self.user.username}) + '?page=2': 2,
        }
        for page, amount in pages_amount.items():
            with self.subTest(page=page):
                response = self.authorized_client.get(page)
                self.assertEqual(len(response.context['page_obj']), amount)

    def test_pages_uses_correct_template(self):
        cache.clear()
        templates_pages_names = {
            'posts/index.html': reverse(INDEX),
            'posts/group_list.html': reverse(GROUP, kwargs={
                'slug': self.group.slug}),
            'posts/profile.html': reverse(PROFILE, kwargs={
                'username': self.user.username}),
            'posts/post_detail.html': reverse(DETAIL, kwargs={
                'post_id': self.post.id}),
            'posts/create_post.html': reverse(CREATE),
            'posts/edit_post.html': reverse(EDIT, kwargs={
                'post_id': self.post.id}),
        }
        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_author.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_home_context(self):
        cache.clear()
        response = self.authorized_client.get(reverse(INDEX))
        first_object = response.context['page_obj'][0]
        post_author_0 = first_object.author
        post_text_0 = first_object.text
        post_image_0 = first_object.image
        self.assertEqual(post_author_0, self.author)
        self.assertEqual(post_text_0, 'Тестовый пост')
        self.assertEqual(post_image_0, '{}'.format(self.post.image.name))

    def test_group_list_context(self):
        cache.clear()
        response = self.authorized_client.get(reverse(GROUP, kwargs={
            'slug': self.group.slug}))
        self.assertEqual(
            response.context.get('group').slug, self.group.slug)
        self.assertEqual(
            response.context['page_obj'][0].image,
            '{}'.format(self.post.image.name)
        )

    def test_profile_context(self):
        cache.clear()
        response = self.authorized_author.get(reverse(PROFILE, kwargs={
            'username': self.author.username}))
        self.assertEqual(
            response.context.get(
                'author').username, self.author.username)
        self.assertEqual(
            response.context['page_obj'][0].image,
            '{}'.format(self.post.image.name)
        )

    def test_post_detail_context(self):
        response = self.authorized_client.get(
            reverse(DETAIL, kwargs={'post_id': self.post.id}))
        self.assertEqual(response.context.get('post').id, self.post.id)
        self.assertEqual(
            response.context['post'].image,
            '{}'.format(self.post.image.name)
        )

    def test_create_form_context(self):
        response = self.authorized_client.get(reverse(CREATE))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.Field,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_edit_form_context(self):
        response = self.authorized_author.get(
            reverse(EDIT, kwargs={'post_id': self.post.id}))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.Field,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_check(self):
        cache.clear()
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый групповой пост',
            'group': self.second_group.id,
        }
        response = self.authorized_author.post(
            reverse(CREATE),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(response, reverse(PROFILE, kwargs={
            'username': self.author.username}))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(Post.objects.filter(
            text='Тестовый групповой пост').exists())
        response = self.authorized_client.get(reverse(INDEX))
        self.assertEqual(
            response.context['page_obj'][0].text, form_data['text']
        )
        response = self.authorized_client.get(reverse(GROUP, kwargs={
            'slug': PostViewTests.second_group.slug}))
        self.assertEqual(
            response.context['page_obj'][0].text, form_data['text']
        )
        response = self.authorized_client.get(reverse(GROUP, kwargs={
            'slug': PostViewTests.group.slug}))
        self.assertEqual(response.context['page_obj'][0].text, self.post.text)

    def test_comments(self):
        """После успешной отправки комментарий появляется на странице поста"""
        comments_count = Comment.objects.count()
        form_data = {
            'text': 'Тестовый комментарий к посту',
        }
        response = self.authorized_client.post(
            reverse(COMMENT, kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(response, reverse(DETAIL, kwargs={
            'post_id': self.post.id}))
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        self.assertTrue(Comment.objects.filter(
            text='Тестовый комментарий к посту').exists())

    def test_cache(self):
        first_response = self.authorized_client.get(reverse(INDEX))
        Post.objects.get(id=self.post.id).delete()
        second_response = self.authorized_client.get(reverse(INDEX))
        self.assertEqual(first_response.content, second_response.content)

    def test_new_post(self):
        # новая запись пользователя появляется в ленте тех,
        # кто на него подписан b не появляетсz в ленте тех, кто не подписан
        cache.clear()
        form_data_1 = {
            'text': 'Пост автора для фолловера',
            'group': self.second_group.id,
        }
        response = self.authorized_author.post(
            reverse(CREATE),
            data=form_data_1,
            follow=True,
        )
        form_data_2 = {
            'text': 'Пост юзера для фолловера',
            'group': self.second_group.id,
        }
        response = self.authorized_client.post(
            reverse(CREATE),
            data=form_data_2,
            follow=True,
        )
        Follow.objects.create(user=self.follower, author=self.author)
        Follow.objects.create(user=self.user, author=self.author)
        Follow.objects.create(user=self.follower, author=self.user)
        response = self.authorized_follower.get(reverse(FOLLOW))
        self.assertEqual(
            response.context['page_obj'][0].text, form_data_2['text']
        )
        response = self.authorized_follower.get(reverse(FOLLOW))
        self.assertEqual(
            response.context['page_obj'][1].text, form_data_1['text']
        )
        response = self.authorized_client.get(reverse(FOLLOW))
        self.assertEqual(
            response.context['page_obj'][0].text, form_data_1['text']
        )
        self.assertNotIn(
            response.context['page_obj'][1].text, form_data_2['text']
        )

    def test_follow_unfollow(self):
        # авторизованный пользователь может подписываться на других
        # пользователей и удалять их из подписок
        follow_count = Follow.objects.count()
        Follow.objects.create(user=self.follower, author=self.author)
        Follow.objects.create(user=self.follower, author=self.user)
        self.assertEqual(Follow.objects.count(), follow_count+2)
        Follow.objects.filter(author=self.author, user=self.follower).delete()
        self.assertEqual(Follow.objects.count(), follow_count+1)

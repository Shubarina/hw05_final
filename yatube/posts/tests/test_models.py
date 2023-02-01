from django.test import TestCase

from posts.models import Group, Post, User


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
            text='Тестовый длинный придлинный текст поста',
        )

    def test_models_have_correct_object_name(self):
        post = PostModelTest.post
        chars = 15
        expected_object_name = post.text[:chars]
        self.assertEqual(expected_object_name, str(post))


class GroupModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )

    def test_models_have_correct_object_name(self):
        group = GroupModelTest.group
        expected_object_name = group.title
        self.assertEqual(expected_object_name, str(group))

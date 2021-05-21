from django.test import TestCase

from posts.models import Group, Post, User


class PostModelTest(TestCase):

    def test_str_method_post_group(self):
        user = User.objects.create_user(username='testuser1')
        post = Post.objects.create(
            text='Тестовый текст поста',
            author=user,
        )
        group = Group.objects.create(
            title='Тестовое название группы',
            description='Тестовое описание группы'
        )
        objects_str_method = {
            post: post.text[:15],
            group: group.title,
        }
        for objects, expected_str in objects_str_method.items():
            with self.subTest(objects=objects):
                self.assertEqual(str(objects), expected_str)

from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post, User


class PostFormTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='testuser')
        cls.group = Group.objects.create(
            title='Тестгруппа',
            slug='test-slug'
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostFormTests.user)

    def test_postform_creates_post(self):
        posts_count = Post.objects.count()
        form_data = {
            'group': PostFormTests.group.id,
            'text': 'Снова тест'
        }
        response = self.authorized_client.post(
            reverse('new_post'), data=form_data, follow=True
        )
        post = Post.objects.first()
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertRedirects(response, reverse('index'))
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.group, PostFormTests.group)
        self.assertEqual(post.author, PostFormTests.user)

    def test_post_edit_form_updates_post(self):
        post = Post.objects.create(
            text='тест текст',
            author=PostFormTests.user,
            group=PostFormTests.group
        )
        group2 = Group.objects.create(
            title='test',
            slug='slug1'
        )
        posts_count = Post.objects.count()
        username = post.author.username
        post_id = post.id
        response = self.authorized_client.post(
            reverse('post_edit',
                    args=(username, post_id)),
            {'text': 'Изменила текст', 'group': group2.id}, follow=True
        )
        post = Post.objects.get(id=post_id)
        self.assertRedirects(
            response, reverse('post', args=(username, post_id))
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertEqual(post.text, 'Изменила текст')
        self.assertEqual(post.group, group2)
        self.assertEqual(post.author, PostFormTests.user)

    def test_unauthorized_client_cannot_create_post(self):
        posts_count = Post.objects.count()
        form_data = {
            'group': PostFormTests.group.id,
            'text': 'Тестирую'
        }
        response = self.client.post(
            reverse('new_post'), data=form_data
        )
        self.assertEqual(Post.objects.count(), posts_count)
        login_page = reverse('login')
        new_post_page = reverse('new_post')
        self.assertRedirects(response, f'{login_page}?next={new_post_page}')

    def test_user_cannot_edit_other_users_post(self):
        user1 = User.objects.create_user(username='test')
        authorized_client = Client()
        authorized_client.force_login(user1)
        group3 = Group.objects.create(
            title='test',
            slug='slug3'
        )
        post = Post.objects.create(
            text='тестовый текст',
            author=PostFormTests.user,
            group=PostFormTests.group
        )
        posts_count = Post.objects.count()
        form_data = {
            'group': group3.id,
            'text': 'текст'
        }
        username = post.author.username
        post_id = post.id
        response = authorized_client.post(
            reverse('post_edit',
                    args=(username, post_id)),
            data=form_data, follow=True
        )
        post = Post.objects.get(id=post_id)
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertRedirects(
            response, reverse('post', args=(username, post_id))
        )
        self.assertNotEqual(post.text, form_data['text'])
        self.assertNotEqual(post.group, form_data['group'])
        self.assertNotEqual(post.author, user1)

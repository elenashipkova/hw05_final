from http import HTTPStatus

from django.test import TestCase, Client
from django.urls import reverse

from posts.models import Group, Post, User


class PostURLTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='username')
        cls.reader = User.objects.create_user(username='notauthor')

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostURLTests.user)
        self.group = Group.objects.create(
            title='test',
            slug='slug'
        )
        self.post = Post.objects.create(
            author=PostURLTests.user,
            text='тестовый текст',
            group=self.group
        )

    def test_url_pages_exists_at_desired_location(self):
        username = self.post.author.username
        post_id = self.post.id
        group_slug = self.group.slug
        url_pages = (
            ('/', self.client),
            (f'/group/{group_slug}/', self.client),
            ('/new/', self.authorized_client),
            (f'/{username}/', self.client),
            (f'/{username}/{post_id}/', self.client),
            (f'/{username}/{post_id}/edit/', self.authorized_client),
        )
        for page, page_client in url_pages:
            with self.subTest(page=page):
                response = page_client.get(page)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_pages_use_correct_name(self):
        username = self.post.author.username
        post_id = self.post.id
        group_slug = self.group.slug
        url_pages_names = (
            ('/', 'index', None),
            (f'/group/{group_slug}/', 'group_posts', (group_slug,)),
            ('/new/', 'new_post', None),
            (f'/{username}/', 'profile', (username,)),
            (f'/{username}/{post_id}/', 'post', (username, post_id)),
            (f'/{username}/{post_id}/edit/', 'post_edit', (username, post_id))
        )
        for page, page_name, args in url_pages_names:
            with self.subTest(page=page):
                self.assertEqual(page, reverse(page_name, args=args))

    def test_url_pages_redirect_users_to_available_pages(self):
        self.authorized_client.force_login(PostURLTests.reader)
        username = self.post.author.username
        post_id = self.post.id
        login_page = reverse('login')
        new_post_page = reverse('new_post')
        post_edit_page = reverse('post_edit', args=(username, post_id))
        redirect_pages_names = (
            ('/new/', self.client, f'{login_page}?next={new_post_page}'),
            (f'/{username}/{post_id}/edit/',
             self.client,
             f'{login_page}?next={post_edit_page}'),
            (f'/{username}/{post_id}/edit/',
             self.authorized_client, f'/{username}/{post_id}/')
        )
        for page, page_client, redirect_page in redirect_pages_names:
            with self.subTest(page=page):
                response = page_client.get(page)
                self.assertRedirects(response, redirect_page)

    def test_page_not_found_error(self):
        response = self.client.get('/group/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

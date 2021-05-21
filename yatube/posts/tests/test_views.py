import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from posts.forms import PostForm
from posts.models import Group, Post, User


class PostPagesTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='testuser1')
        cls.group = Group.objects.create(title='Тестгруппа',
                                         description='описание',
                                         slug='slug')
        cls.post = Post.objects.create(text='тестовый текст',
                                       author=cls.user,
                                       group=cls.group)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostPagesTests.user)

    def test_paginator_pages(self):
        many_posts = [
            Post(
                text=f'{post} пусть будет так',
                author=PostPagesTests.user,
                group=PostPagesTests.group
            )
            for post in range(13)
        ]
        Post.objects.bulk_create(many_posts)

        response = self.client.get(reverse('index'))
        self.assertEqual(
            len(response.context.get('page').object_list),
            settings.POSTS_PER_PAGE
        )

    def test_pages_use_correct_template(self):
        group_slug = PostPagesTests.group.slug
        username = PostPagesTests.post.author.username
        post_id = PostPagesTests.post.id
        templates_pages_names = (
            ('posts/index.html', 'index', None),
            ('posts/group.html', 'group_posts', (group_slug,)),
            ('posts/new.html', 'new_post', None),
            ('posts/new.html', 'post_edit', (username, post_id)),
            ('posts/profile.html', 'profile', (username,)),
            ('posts/post.html', 'post', (username, post_id))
        )
        for template, reverse_name, args in templates_pages_names:
            with self.subTest(template=template):
                response = self.authorized_client.get(
                    reverse(reverse_name, args=args)
                )
                self.assertTemplateUsed(response, template)

    def checking_post_context_parameters(self, context_data, object_type):
        self.assertIn(object_type, context_data)
        if object_type == 'page':
            post = context_data['page'][0]
        else:
            post = context_data['post']
        self.assertEqual(post.text, PostPagesTests.post.text)
        self.assertEqual(post.author, PostPagesTests.post.author)
        self.assertEqual(post.pub_date, PostPagesTests.post.pub_date)
        self.assertEqual(post.group, PostPagesTests.post.group)

    def test_homepage_shows_correct_context(self):
        response = self.client.get(reverse('index'))
        self.checking_post_context_parameters(response.context, 'page')

    def test_group_pages_show_correct_context(self):
        group = PostPagesTests.group
        group_page = reverse('group_posts', args=(group.slug,))
        response = self.client.get(group_page)
        self.checking_post_context_parameters(response.context, 'page')
        self.assertIn('group', response.context)
        self.assertEqual(response.context['group'].title, group.title)
        self.assertEqual(
            response.context['group'].description, group.description
        )

    def test_group_post_appears_on_correct_group_page_and_homepage(self):
        group_1 = Group.objects.create(title='группа',
                                       description='о',
                                       slug='slug_1')
        group_1_page = reverse('group_posts', args=(group_1.slug,))
        resp_group_1 = self.authorized_client.get(group_1_page)
        self.assertEqual(len(resp_group_1.context['page']), 0)
        response = self.authorized_client.get(reverse('index'))
        self.assertEqual(
            response.context['page'][0].text, PostPagesTests.post.text
        )
        self.assertEqual(len(response.context['page']), 1)

    def test_new_post_page_shows_correct_context(self):
        response = self.authorized_client.get(reverse('new_post'))
        self.assertIn('form', response.context)
        self.assertIn('edit', response.context)
        self.assertIsInstance(response.context['form'], PostForm)
        self.assertIs(response.context['edit'], False)

    def test_profile_page_shows_correct_context(self):
        username = PostPagesTests.user.username
        profile_page = reverse('profile', args=(username,))
        response = self.client.get(profile_page)
        self.checking_post_context_parameters(response.context, 'page')
        self.assertIn('profile', response.context)
        self.assertEqual(response.context['profile'], PostPagesTests.user)

    def test_post_view_page_shows_correct_context(self):
        username = PostPagesTests.user.username
        post_id = PostPagesTests.post.id
        post_page = reverse('post', args=(username, post_id))
        response = self.client.get(post_page)
        self.checking_post_context_parameters(response.context, 'post')
        self.assertIn('author', response.context)
        self.assertEqual(
            response.context['author'], PostPagesTests.post.author
        )

    def test_post_edit_page_shows_correct_context(self):
        username = PostPagesTests.user.username
        post_id = PostPagesTests.post.id
        post_edit_page = reverse('post_edit', args=(username, post_id))
        response = self.authorized_client.get(post_edit_page)
        self.checking_post_context_parameters(response.context, 'post')
        self.assertIn('form', response.context)
        self.assertIn('edit', response.context)
        self.assertIsInstance(response.context['form'], PostForm)
        self.assertIs(response.context['edit'], True)

    def test_image_post_appears_on_pages(self):
        group_im = Group.objects.create(title='Images',
                                        description='I',
                                        slug='slug_im')
        im_post = Post.objects.create(text='тест картинки',
                                       author=PostPagesTests.user,
                                       group=group_im)
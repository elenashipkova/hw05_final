import shutil
import tempfile

from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.forms import CommentForm, PostForm
from posts.models import Follow, Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.user = User.objects.create_user(username='testuser1')
        cls.group = Group.objects.create(title='Тестгруппа',
                                         description='описание',
                                         slug='slug')
        cls.post = Post.objects.create(text='тестовый текст',
                                       author=cls.user,
                                       group=cls.group,
                                       image=uploaded)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

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
            for post in range(settings.POSTS_PER_PAGE * 2)
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
        self.assertEqual(post.image, PostPagesTests.post.image)

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
        self.assertIn('following', response.context)
        self.assertEqual(response.context['profile'], PostPagesTests.user)
        self.assertEqual(response.context['following'], False)

    def test_post_view_page_shows_correct_context(self):
        username = PostPagesTests.user.username
        post_id = PostPagesTests.post.id
        post_page = reverse('post', args=(username, post_id))
        response = self.client.get(post_page)
        self.checking_post_context_parameters(response.context, 'post')
        self.assertIn('comments', response.context)
        self.assertIn('form', response.context)
        self.assertIsInstance(response.context['form'], CommentForm)

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

    def test_cache_page(self):
        response_0 = self.client.get(reverse('index'))
        cache_page = response_0.content
        Post.objects.create(text='test cache', author=PostPagesTests.user)
        response_1 = self.client.get(reverse('index'))
        update_page = response_1.content
        self.assertEqual(cache_page, update_page)
        cache.clear()
        response = self.client.get(reverse('index'))
        actual_page = response.content
        self.assertNotEqual(actual_page, cache_page)


class FollowTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='Автор')
        cls.follower = User.objects.create_user(username='Подписчик')
        cls.guest = User.objects.create_user(username='Гость')
        cls.post1 = Post.objects.create(text='тест подписок',
                                        author=cls.author)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(FollowTests.author)

    def test_auth_user_can_follow_authors(self):
        authorized_follower = Client()
        authorized_follower.force_login(FollowTests.follower)
        author_username = FollowTests.author.username
        follow_count = Follow.objects.count()
        authorized_follower.get(
            reverse('profile_follow', args=(author_username,))
        )
        follow = Follow.objects.first()
        self.assertEqual(Follow.objects.count(), follow_count + 1)
        self.assertEqual(follow.author, FollowTests.author)
        self.assertEqual(follow.user, FollowTests.follower)

    def test_auth_user_can_unfollow(self):
        authorized_follower = Client()
        authorized_follower.force_login(FollowTests.follower)
        author_username = FollowTests.author.username
        Follow.objects.create(
            author=FollowTests.author, user=FollowTests.follower)
        follow_count = Follow.objects.filter(
            author=FollowTests.author, user=FollowTests.follower).count()
        authorized_follower.get(
            reverse('profile_unfollow', args=(author_username,))
        )
        count = Follow.objects.filter(
            author=FollowTests.author, user=FollowTests.follower).count()
        self.assertEqual(count, follow_count - 1)

    def test_authors_post_appears_at_follow_index(self):
        authorized_follower = Client()
        authorized_follower.force_login(FollowTests.follower)
        Follow.objects.create(
            author=FollowTests.author, user=FollowTests.follower)
        response = authorized_follower.get(reverse('follow_index'))
        self.assertEqual(response.context['page'][0], FollowTests.post1)

    def test_authors_post_not_shown_to_unfollows(self):
        authorized_reader = Client()
        authorized_reader.force_login(FollowTests.guest)
        response = authorized_reader.get(reverse('follow_index'))
        self.assertEqual(len(response.context.get('page').object_list), 0)

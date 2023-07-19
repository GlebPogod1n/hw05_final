import shutil
import tempfile

from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.core.cache import cache
from django import forms
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile

from posts.models import Post, Group, User, Follow, Comment
from yatube.settings import CONST


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='User')
        cls.post_author = User.objects.create_user(username='post_author')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            description='Тестовое описание',
            slug='test-slug'
        )
        cls.group_2 = Group.objects.create(
            title='Тестовый заголовок2',
            description='Тестовое описание2',
            slug='test-slug2',
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        for i in range(12):
            Post.objects.create(
                author=cls.user,
                group=cls.group_2,
                text=f'Тестовый пост №{i+1} в группе 2',
                image=cls.uploaded,
            )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.post = Post.objects.create(
            author=self.user,
            group=self.group,
            text='Тест пост в группе 1',
            image=self.uploaded,
        )
        self.comment = Comment.objects.create(
            author=self.user,
            text='Тестовый комментарий',
            post=self.post
        )
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.post_author_client = Client()
        self.post_author_client.force_login(self.post_author)
        cache.clear()

    def test_url_templates(self):
        urls = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': self.group.slug}):
            'posts/group_list.html',
            reverse('posts:profile', args={self.user}):
            'posts/profile.html',
            reverse('posts:post_detail', args=[self.post.pk]):
            'posts/post_detail.html',
            reverse('posts:post_edit', args=[self.post.pk]):
            'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('about:author'): 'about/author.html',
            reverse('about:tech'): 'about/tech.html',
            reverse('posts:follow_index'): 'posts/follow.html',
        }
        for reverse_name, template in urls.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_correct_context_(self):
        urls = (
            reverse('posts:index'),
            reverse(
                'posts:group_list', kwargs={'slug': self.group.slug}),
            reverse(
                'posts:profile', args={self.user}),
        )
        for url in urls:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                context_post = response.context['page_obj'][0]
            PostPagesTests.get_assert_context(self, context_post)

    def get_assert_context(self, context_post):
        obj = {
            context_post.author.username: self.user.username,
            context_post.group.title: self.group.title,
            context_post.text: self.post.text,
            context_post.author.id: 1,
            context_post.group.id: 1,
            context_post.image.size: Post.objects.last().image.size,
        }
        for respo, rever in obj.items():
            with self.subTest(respo=respo):
                self.assertEqual(respo, rever)

    def test_group_context(self):
        url = reverse('posts:group_list', kwargs={'slug': self.group.slug})
        response = self.authorized_client.get(url)
        context_group = response.context['group'].title

        self.assertEqual(context_group, self.group.title)

    def test_profile_correct_context(self):
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': self.user.username})
        )
        context_author = response.context['author'].username

        self.assertEqual(context_author, self.user.username)

    def test_post_detail_page_show(self):
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.pk})
        )
        context_post = response.context['post']
        context_comment = response.context.get('comments')[0]

        self.assertEqual(context_comment, self.comment)
        PostPagesTests.get_assert_context(self, context_post)

    def test_post_create_context(self):
        fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
        }
        response = self.authorized_client.get(reverse('posts:post_create'))
        form = response.context['form']

        for field, expected in fields.items():
            with self.subTest(field=field):
                self.assertIsInstance(form.fields[field], expected)

    def test_post_edit_context(self):
        url = reverse('posts:post_edit', kwargs={'post_id': self.post.pk})
        response = self.authorized_client.get(url)
        form = response.context['form']

        context = {
            'form': form,
            'is_edit': True,
            'post': self.post
        }

        for value, expected in context.items():
            with self.subTest(value=value):
                self.assertEqual(response.context[value], expected)

        fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
        }

        for field, expected in fields.items():
            with self.subTest(field=field):
                self.assertIsInstance(form.fields[field], expected)

    def test_post_correct_appear(self):
        pages_names = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.user.username}),
        ]

        for page in pages_names:
            with self.subTest(page=page):
                response = self.authorized_client.get(page)
                context_post = response.context['page_obj'][0]

                self.assertEqual(context_post, self.post)

    def test_post_correct_not_appear(self):
        page = reverse('posts:group_list', kwargs={'slug': self.group_2.slug})
        response = self.authorized_client.get(page)
        context_post = response.context['page_obj'][0]

        self.assertNotEqual(context_post, self.post)

    def test_posts_pages_correct_paginator_work(self):
        urls_page2posts_names = {
            reverse('posts:index'):
            (Post.objects.count() - CONST),
            reverse('posts:group_list', kwargs={'slug': self.group_2.slug}):
            Group.objects.count(),
            reverse('posts:profile', kwargs={'username': self.user}):
            (Post.objects.count() - CONST),
        }

        for page, page_2_posts in urls_page2posts_names.items():
            with self.subTest(page=page):
                response_page_1 = self.authorized_client.get(page)
                response_page_2 = self.authorized_client.get(page + '?page=2')

                self.assertEqual(
                    len(response_page_1.context['page_obj']), CONST
                )
                self.assertEqual(
                    len(response_page_2.context['page_obj']),
                    page_2_posts
                )

    def test_cach(self):
        page_content = self.client.get(reverse('posts:index')).content
        self.post.delete()
        cached_content = self.client.get(reverse('posts:index')).content
        self.assertEqual(page_content, cached_content)
        cache.clear()
        cleared_cache = self.client.get(reverse('posts:index')).content
        self.assertNotEqual(cached_content, cleared_cache)

    def test_authorized_user_subscribe(self):
        self.authorized_client.get(
            reverse('posts:profile_follow', args=['post_author'])
        )
        self.assertTrue(
            Follow.objects.filter(user=self.user,
                                  author=self.post_author).exists()
        )

    def test_authorized_user_subscribe_off(self):
        self.authorized_client.get(
            reverse('posts:profile_follow', args=['post_author'])
        )
        self.authorized_client.get(
            reverse('posts:profile_unfollow', args=['post_author'])
        )
        self.assertFalse(
            Follow.objects.filter(user=self.user,
                                  author=self.post_author).exists()
        )

    def test_follow_index_view(self):
        new_post_author = Post.objects.create(
            text='Авторский текст',
            author=self.post_author,
            group=self.group
        )
        response = self.authorized_client.get(
            reverse('posts:follow_index')
        )
        first_object = response.context.get('page_obj')
        self.assertNotEqual(first_object, new_post_author)
        Follow.objects.create(user=self.user, author=self.post_author)
        response = self.authorized_client.get(
            reverse('posts:follow_index')
        )
        second_object = response.context.get('page_obj').object_list[0]
        self.assertEqual(second_object, new_post_author)

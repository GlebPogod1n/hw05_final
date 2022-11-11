from http import HTTPStatus

from django.test import TestCase, Client
from django.urls import reverse

from posts.models import Post, Group, User


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            description='Тестовое описание',
            slug='test-slug',
        )
        cls.user = User.objects.create(username='User')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
            group=cls.group,
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.user_not_author = User.objects.create(
            username='user_not_author')
        self.authorized_not_author = Client()
        self.authorized_not_author.force_login(self.user_not_author)

    def test_urls_uses_correct_template(self):
        url_templates_names = {
            '/': 'posts/index.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.user}/': 'posts/profile.html',
            f'/posts/{self.post.pk}/': 'posts/post_detail.html',
            f'/posts/{self.post.pk}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
        }
        for url, template in url_templates_names.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_urls_allowed_for_guests(self):
        urls = {
            '/',
            f'/group/{self.group.slug}/',
            f'/profile/{self.user}/',
            f'/posts/{self.post.pk}/',
            reverse('about:author'),
            reverse('about:tech'),
        }
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_task_list_url_redirect_anonymous_on_admin_login(self):
        response = self.client.get('/create/', follow=True)
        self.assertRedirects(
            response, '/auth/login/?next=/create/')

    def test_url_exists_at_desired_location(self):
        response = self.authorized_not_author.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_url_exists_at_desired_location_authors(self):
        response = self.authorized_client.get(f'/posts/{self.post.pk}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_task_list_url_redirect_authorized_not_author(self):
        response = self.authorized_not_author.get(
            f'/posts/{self.post.pk}/edit/', follow=True)
        self.assertRedirects(
            response, f'/posts/{self.post.pk}/')

    def test_404_not_found_and_custom(self):
        response = self.client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertTemplateUsed(response, 'core/404.html')

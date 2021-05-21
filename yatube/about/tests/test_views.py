from django.test import TestCase
from django.urls import reverse


class AboutViewsTests(TestCase):

    def test_about_urls_use_correct_template(self):
        templates_path_names = (
            ('about/author.html', 'about:author'),
            ('about/tech.html', 'about:tech'),
        )
        for template, path_name in templates_path_names:
            with self.subTest(template=template):
                response = self.client.get(reverse(path_name))
                self.assertTemplateUsed(response, template)

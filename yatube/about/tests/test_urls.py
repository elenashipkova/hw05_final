from http import HTTPStatus

from django.test import TestCase
from django.urls import reverse


class AboutURLTests(TestCase):

    def test_about_urls_exist_at_desired_location_and_use_correct_name(self):
        url_address_names = (
            ('/about/author/', 'about:author'),
            ('/about/tech/', 'about:tech'),
        )
        for address, name in url_address_names:
            with self.subTest(address=address):
                response = self.client.get(address)
                self.assertEqual(address, reverse(name))
                self.assertEqual(response.status_code, HTTPStatus.OK)

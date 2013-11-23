import q

from django.test import TestCase
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse


class AccountModelsTest(TestCase):

    def setUp(self):
        user = User.objects.create(username='Account')
        user.save()
        
    def test_testing(self):
        user = User.objects.get(username="Account")
        self.assertEqual(user.username, "Account")
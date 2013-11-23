import q
import requests
import re
import facebook

from django.conf import settings
from django.test import TestCase
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.core import mail
from django.contrib.sites.models import Site

from allauth.socialaccount import providers
from allauth.socialaccount import app_settings

from idios import views
from ..socialaccount.models import SocialApp


class AccountViewsTest(TestCase):

    def setUp(self):
        site = Site.objects.get(pk=1)
        app_info = {"site": site,
                    "provider": "Facebook",
                    "name": "LinerNotes",
                    "key": settings.FACEBOOK_APP_ID,
                    "secret": settings.FACEBOOK_APP_SECRET,
                    "id": 1} # compensate for # hack for debug facebook app
        app = SocialApp(**app_info)
        app.save()

    def test_send_email(self):
        # Send message.
        mail.send_mail('Subject here', 'Here is the message.',
            'from@example.com', ['to@example.com'],
            fail_silently=False)

        # Test that one message has been sent.
        self.assertEqual(len(mail.outbox), 1)

        # Verify that the subject of the first message is correct.
        self.assertEqual(mail.outbox[0].subject, 'Subject here')

    def test_signup(self):
        url = reverse("account_signup")
        # get should render signup page
        req = self.client.get(url)
        self.assertEqual(req.status_code, 200)
        self.assertTemplateUsed(req, "account/signup.html")
        self.assertIn("Already have", req.content)
        # post should create a user
        sample_data = {"password2": "testpass",
                       "password1": "testpass",
                       "username": "testuser",
                       "email": "test@testing.com",}
        req = self.client.post(url, sample_data)
        self.assertEqual(req.status_code, 302)
        self.assertTemplateUsed(req, "account/email/email_confirmation_subject.txt")
        self.confirm_email()
        self.try_login()
        self.confirm_redirect()

    def test_facebook_user_create(self):
        user_token = self.get_facebook_user()
        login_url = reverse("facebook_login_by_token")
        login_req = self.client.post(login_url, {"access_token": user_token}, follow=True)
        print login_req.redirect_chain
        sign_url = login_req.redirect_chain[0][0]
        data = {"username": "testuser",
                "email": "test@test.com"}
        self.assertEqual(login_req.status_code, 200)
        print sign_url, data
        sign_req = self.client.post(sign_url, data)
        self.confirm_email()
        login_req = self.client.post(login_url, {"access_token": user_token}, follow=True)
        self.assertEqual(login_req.status_code, 200)
        print "LOOOOG {}".format(login_req.content)
        self.facebook_like_import()


    def test_email_send(self):
        pass

    def test_email_confirm(self):
        pass

    @classmethod
    def get_facebook_user(self):
        token_string = "https://graph.facebook.com/oauth/access_token"
        app_id = settings.FACEBOOK_APP_ID
        params = {
                  "client_id": app_id,
                  "client_secret": settings.FACEBOOK_APP_SECRET,
                  "grant_type": "client_credentials",
                  "redirect_uri": "http://www.linernotes.com",
                  }
        req = requests.get(token_string, params=params)
        token = req.text.split("=")[1]
        test_user_string = "https://graph.facebook.com/{}/accounts/test-users".\
                            format(app_id)
        params = {"installed": "true",
          "name": "testuser",
          "locale": "en_US",
          "permissions": app_settings.PROVIDERS["facebook"]["SCOPE"],
          "access_token": token,
          }
        user_response = requests.post(test_user_string, params=params)
        user_token = user_response.json()["access_token"]
        return user_token

    def try_login(self):
        # logout since email process logged us in
        url = reverse("account_logout")
        # get should render login page
        req = self.client.get(url)
        self.assertEqual(req.status_code, 200)
        # try logging in
        url = reverse("account_login")
        # get should render login page
        req = self.client.get(url)
        self.assertEqual(req.status_code, 200)
        self.assertTemplateUsed(req, "account/login.html")
        self.assertIn("have an account", req.content)
        # post should login
        sample_data = {"password": "testpass",
                       "login": "testuser",
                       }
        req = self.client.post(url, sample_data)
        self.assertEqual(req.status_code, 302)
        #self.assertTemplateUsed(req, "home.html")
        # log back out
        url = reverse("account_logout")
        # get should render login page
        req = self.client.get(url)
        self.assertEqual(req.status_code, 200)

    def confirm_email(self):
        # confirm email
        msg_body = mail.outbox[0].body
        key = re.search("email/(.*?)/", msg_body).group(1)
        conf_url = reverse("account_confirm_email", kwargs={"key": key})
        conf_req = self.client.post(conf_url, {"key": key}, follow=True)
        self.assertEqual(conf_req.status_code, 200)
        self.assertTemplateUsed(conf_req, "homepage.html")
        
    def facebook_like_import(self):
        """
        view is in idios, but requires elaborate social account setup 
        to work so testing here
        """
        url = reverse("facebook_import_by_username",
                      kwargs={"username": "testuser"})
        print "trying URL {}".format(url)
        req = self.client.get(url, follow=True)
        print "like import content:", req.content
        # TODO rogueleaderr create a sample actual import so the board check doesn't 404
        #self.assertEqual(req.status_code, 200)
        #self.assertIn("Testuser's Profile", req.content)

    def confirm_redirect(self):
        url = reverse("facebook_next")
        # should go home because user has no prior visits
        req = self.client.get(url, follow=True)
        self.assertEqual(req.status_code, 200)
        self.assertTemplateUsed(req, "homepage.html")
        self.assertIn("start learning", req.content)


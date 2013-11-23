from crispy_forms.layout import Layout, Field, HTML, Fieldset, Div
from django.contrib.formtools.wizard.views import SessionWizardView
from django.contrib.localflavor.us.forms import USZipCodeField
from django.forms import ModelForm, HiddenInput

from crispy_forms.helper import FormHelper
from profiles.models import Profile
from idios.views import start_lastfm_import
from django.shortcuts import redirect

import account.app_settings
from account.utils import complete_signup
from favorites.favorites_helpers import make_favorite

__author__ = 'rogueleaderr'

from django import forms


class ProfileSetupForm1(ModelForm):

    zipcode = USZipCodeField(required=False)

    class Meta:
        model = Profile
        fields = ["username", "name", "location", "country", "gender", "age", "receive_digests"]


class ProfileSetupForm2(forms.Form):
    facebook = forms.BooleanField(required=False)
    spotify = forms.BooleanField(required=False)
    lastfm = forms.CharField(max_length=100, required=False)


class ProfileSetupForm3(forms.Form):

    band_1 = forms.CharField(max_length=100, required=False)
    band_2 = forms.CharField(max_length=100, required=False)
    band_3 = forms.CharField(max_length=100, required=False)
    band_4 = forms.CharField(max_length=100, required=False)
    band_5 = forms.CharField(max_length=100, required=False)

    band_id_1 = forms.CharField(widget=HiddenInput)
    band_id_2 = forms.CharField(widget=HiddenInput)
    band_id_3 = forms.CharField(widget=HiddenInput)
    band_id_4 = forms.CharField(widget=HiddenInput)
    band_id_5 = forms.CharField(widget=HiddenInput)

    def __init__(self, *args, **kwargs):
        super(ProfileSetupForm3, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.label_class = 'col-lg-2'
        self.helper.field_class = 'col-lg-10'
        self.form_tag = False
        self.helper.layout = Layout(
            Fieldset(
                "<p>All you have to do is tell us <strong>five</strong> bands that you like</p>",
                Div(Field("band_1", css_class="band-typeahead"),
                    css_class="row col-sm-12"),
                Div(Field("band_2", css_class="band-typeahead"),
                    css_class="row col-sm-12"),
                Div(Field("band_3", css_class="band-typeahead"),
                    css_class="row col-sm-12"),
                Div(Field("band_4", css_class="band-typeahead"),
                    css_class="row col-sm-12"),
                Div(Field("band_5", css_class="band-typeahead"),
                    css_class="row col-sm-12"),
                Field("band_id_1"),
                Field("band_id_2"),
                Field("band_id_3"),
                Field("band_id_4"),
                Field("band_id_5"),
                )
            )


class ProfileSetupForm4(forms.Form):
    email = forms.EmailField()





FORMS = [("initial_info", ProfileSetupForm1),
         ("import_names", ProfileSetupForm2),
         ("favorite_bands", ProfileSetupForm3),
         ]

TEMPLATES = {k[0]: "account/signup_form_{}.html".format(i+1) for i,k in enumerate(FORMS)}


class ProfileSetupWizard(SessionWizardView):
    def get_template_names(self):
        return [TEMPLATES[self.steps.current]]

    def done(self, form_list, **kwargs):
        request = self.request
        profile_data = form_list[0].cleaned_data
        profile = Profile.objects.get(user=request.user)
        for k,v in profile_data.items():
            if v:
                profile.__dict__[k] = v
        profile.signup_complete = True
        import_form = form_list[1]
        if import_form.cleaned_data["lastfm"]:
            start_lastfm_import(import_form.cleaned_data["lastfm"], request.user)
            profile.lastfm_artists_imported = True
        profile.save()
        try:
            fav_form = form_list[2]
            for item in ["band_id_{}".format(x) for x in range(1,5)]:
                fav_uri = fav_form.cleaned_data[item]
                # TODO rogueleaderr use models instead of tags for this
                make_favorite(self.request.user, fav_uri, tags=["$top_5_artists"])
        except IndexError:
            pass
        return redirect("what_next")

#-------- helper functions

def external_import_selected(wizard):
    # see if any external imports were selected
    cleaned_data = wizard.get_cleaned_data_for_step('import_names') or {}
    imports_selected = not any([v for v in cleaned_data.values()])
    return imports_selected
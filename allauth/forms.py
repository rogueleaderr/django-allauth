from crispy_forms.layout import Layout, Field, HTML, Fieldset, Div, Submit
from django.contrib.formtools.wizard.views import SessionWizardView
from django.contrib.localflavor.us.forms import USZipCodeField
from django.forms import ModelForm, HiddenInput, BooleanField

from crispy_forms.helper import FormHelper
from profiles.models import Profile
from idios.views import start_lastfm_import, set_initial_type_positions
from django.shortcuts import redirect

import account.app_settings
from account.utils import complete_signup
from favorites.favorites_helpers import make_favorite

__author__ = 'rogueleaderr'

from django import forms


class ProfileSetupForm1(ModelForm):

    zipcode = USZipCodeField(required=False)


    def __init__(self, *args, **kwargs):
        super(ProfileSetupForm1, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.form_tag = False
        self.helper.layout = Layout(
            Fieldset(
                Div(Field("dumb", placeholder="Name", css_class="search_box"), css_class="row"),
                Div(Field("name", placeholder="Name", css_class="search_box"), css_class="row"),
                Div(Field("age", placeholder="Age", css_class="col-lg-6"),
                    Field("gender", css_class="col-lg-6 dropdown-select selecte-sub"),
                    css_class="row"
                ),
                Div(Field("country", css_class="col-lg-12 dropdown-select"), css_class="row"),
                Div(Div(Field("zipcode", placeholder="Zipcode", css_class="search_box"), css_class="col-lg-6"), css_class="row"),
                Div(Div(HTML("<p>By default, your profile will be publicly visible so you can show of your great taste to the world. </p>"),
                        css_class="col-lg-12"),
                    Div(HTML("<h4>To hide your profile check this box :</h4>"),
                        Field("private", css_class="checkbox-myClass"),

                        css_class="col-lg-12"),
                    Div(HTML("<p>Linernotes can send you occasional helpful emails letting you know about concerts, new releases, great playlists etc. </p>"),
                        css_class="col-lg-12"),
                    Div(HTML("<h4>To receive these emails check here :</h4>"),
                        Field("receive_digests", css_class="checkbox-myClass"),
                        css_class="col-lg-12"),
                    css_class="row text-left sub-wrap"
                ),
            )
        )
        self.helper.add_input(Submit('submit', 'Next Step', css_class="btn primary"))

    class Meta:
        model = Profile
        fields = ["name", "country", "gender", "age", "private", "receive_digests"]
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Name', 'class': 'text_input_box',}),
            'age': forms.TextInput(attrs={'placeholder': 'Age', 'class': 'text_input_box',}),
            'gender': forms.Select(attrs={'class': 'selectyze1', "name": "style1"}),
            'country': forms.Select(attrs={'class': 'selectyze1', "name": "style1"}),
            'zipcode': forms.TextInput(attrs={'placeholder': 'Zipcode', 'class': 'text_input_box',}),
            'private': forms.CheckboxInput(attrs={'class': 'checkbox-myClass',}),
            'receive_digests': forms.CheckboxInput(attrs={'class': 'checkbox-myClass',}),
        }


class ProfileSetupForm2(forms.Form):
        lastfm = forms.CharField(max_length=100, required=False,
                                 widget=forms.TextInput(attrs={'placeholder': 'Last.fm Username'}))

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

        self.helper.field_class = 'col-lg-12'
        self.form_tag = False
        self.helper.layout = Layout(
            Fieldset(
                "",  # no legend
                Div(Field("band_1", css_class="band-typeahead", placeholder="#1"),
                    css_class="row col-sm-12"),
                Div(Field("band_2", css_class="band-typeahead", placeholder="#2"),
                    css_class="row col-sm-12"),
                Div(Field("band_3", css_class="band-typeahead", placeholder="#3"),
                    css_class="row col-sm-12"),
                Div(Field("band_4", css_class="band-typeahead", placeholder="#4"),
                    css_class="row col-sm-12"),
                Div(Field("band_5", css_class="band-typeahead", placeholder="#5"),
                    css_class="row col-sm-12"),
                Field("band_id_1"),
                Field("band_id_2"),
                Field("band_id_3"),
                Field("band_id_4"),
                Field("band_id_5"),
                )
            )
        self.helper.add_input(Submit('submit', "I'm Finished (Woohoo)", css_class="btn2"))


class ProfileSetupForm4(forms.Form):
    email = forms.EmailField()





FORMS = [("initial_info", ProfileSetupForm1),
         ("import_names", ProfileSetupForm2),
         ("favorite_bands", ProfileSetupForm3),
         ]

TEMPLATES = {k[0]: "forms/signup_form_{}.html".format(i+1) for i,k in enumerate(FORMS)}


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
            order = []
            for item in ["band_id_{}".format(x) for x in range(1,5)]:
                fav_uri = fav_form.cleaned_data[item]
                make_favorite(request.user, fav_uri)
                order.append(fav_uri)
                # TODO rogueleaderr use models instead of tags for this
            set_initial_type_positions(self.request.user, order, "music-artist")
        except IndexError:
            pass
        return redirect("what_next")

#-------- helper functions

def external_import_selected(wizard):
    # see if any external imports were selected
    cleaned_data = wizard.get_cleaned_data_for_step('import_names') or {}
    imports_selected = not any([v for v in cleaned_data.values()])
    return imports_selected
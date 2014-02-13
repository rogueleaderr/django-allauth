from crispy_forms.layout import Layout, Field, HTML, Fieldset, Div, Submit
from django.contrib import messages
from django.contrib.formtools.wizard.views import SessionWizardView
from django.contrib.localflavor.us.forms import USZipCodeField
from django.core.exceptions import ObjectDoesNotExist
from django.forms import ModelForm, HiddenInput
from crispy_forms.helper import FormHelper
from django.shortcuts import redirect

from profiles.models import Profile
from allauth.socialaccount.models import SocialAccount
from idios.views import start_lastfm_import, set_initial_type_positions, start_facebook_artist_import
from favorites.favorites_helpers import make_favorite


__author__ = 'rogueleaderr'

from django import forms


class ProfileSetupForm1(ModelForm):

    zipcode = USZipCodeField(required=False, widget=forms.TextInput(attrs={'placeholder': 'Zipcode',
                                                                           'class': 'text_input_box',}))

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
            'private': forms.CheckboxInput(attrs={'class': 'checkbox-myClass',}),
            'receive_digests': forms.CheckboxInput(attrs={'class': 'checkbox-myClass',}),
        }


class ProfileSetupForm2(forms.Form):
        lastfm = forms.CharField(max_length=100, required=False,
                                 widget=forms.TextInput(attrs={'placeholder': 'Last.fm Username',
                                                               'class': 'text_input_box',}))

        """
        def __init__(self, *args, **kwargs):
            if "real_name" in kwargs:
                self.real_name = kwargs.pop("real_name")
            import pdb ; pdb.set_trace()
            super(ProfileSetupForm2, self).__init__(*args, **kwargs)
        """


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

    def __init__(self, *args, **kwargs):
        super(ProfileSetupWizard, self).__init__(*args, **kwargs)
        self.imports_to_run = {}

    def get_template_names(self):
        return [TEMPLATES[self.steps.current]]

    """
    def get_form_kwargs(self, step=None):
        kwargs = {}
        print("STPP", step)
        if step == 'import_names':
            try:
                real_name = self.get_cleaned_data_for_step('initial_info')['name']
                kwargs.update({'real_name': real_name,})
                print("UPTT", kwargs)
            except TypeError:  # hack to get around the fact that this is called each step to check for band importer selection
                pass

        return kwargs
    """

    def get_context_data(self, form, **kwargs):
        context = super(ProfileSetupWizard, self).get_context_data(form=form, **kwargs)
        if self.steps.current == "import_names":
            real_name = self.get_cleaned_data_for_step('initial_info')['name']
            try:
                social = SocialAccount.objects.get(user=self.request.user,
                                                 provider="facebook")
                fb_connected = True
            except ObjectDoesNotExist:
                fb_connected = False
            context.update({'real_name': real_name,
                            'fb_connected': fb_connected})

        return context




    def done(self, form_list, **kwargs):
        request = self.request
        profile_data = form_list[0].cleaned_data
        profile = Profile.objects.get(user=request.user)
        for k,v in profile_data.items():
            if v:
                profile.__dict__[k] = v
        profile.signup_complete = True
        import_form = form_list[1]
        if "facebook" in self.imports_to_run:
            what_next = start_facebook_artist_import(self.imports_to_run["facebook"])
        elif "spotify" in self.imports_to_run:
            what_next = start_spotify_import(self.imports_to_run["spotify"])
        elif "lastfm" in self.imports_to_run:
            cleaned_data = self.get_cleaned_data_for_step('import_names') or {}
            if "lastfm" in cleaned_data:
                what_next = start_lastfm_import(cleaned_data["lastfm"],
                                    self.imports_to_run["lastfm"])
                profile.lastfm_artists_imported = True
                print("LASST start")
            else:
                import pdb ; pdb.set_trace()
        else:
            messages.add_message(request, messages.INFO, "Added your top 5 artists to your collection. Check them out below!")
            what_next = redirect("what_next")



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
        return what_next

#-------- helper functions




def external_import_selected(wizard):
    # see if any external imports were selected

    #
    # if import fails, fail back to manual select screen
    imports_selected = True
    # make sure this the right step
    try:
        # throw exception is wrong step or not a POST
        if not wizard.request.POST["profile_setup_wizard-current_step"] == "import_names":
            raise KeyError
    except (KeyError, AttributeError) as e:
        print e
        return imports_selected
    profile = Profile.objects.get(user=wizard.request.user)
    # .x because apparently image submit button appends to name
    # trigger the selected import process, confirm that it succeeds.
    if "facebook.x" in wizard.request.POST:
        wizard.imports_to_run["facebook"] = wizard.request
        imports_selected = False
    elif "spotify.x" in wizard.request.POST:
        wizard.imports_to_run["spotify"] = wizard.request
        imports_selected = False
    elif "lastfm" in wizard.request.POST:
        wizard.imports_to_run["lastfm"] = wizard.request
        imports_selected = False


    # if import succeeds, end process
    return imports_selected
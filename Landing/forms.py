from django.forms import CharField, TextInput, PasswordInput, ModelForm, ValidationError
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.utils.translation import ugettext as _
from django.contrib.auth import get_user_model

from snowpenguin.django.recaptcha2.fields import ReCaptchaField
from snowpenguin.django.recaptcha2.widgets import ReCaptchaWidget

from Visitor.models import Profile


User = get_user_model()

class EventAuthForm(AuthenticationForm):
    username = CharField(label="Username",
                         widget=TextInput(attrs={'class': 'form-control',
                                                 'placeholder': 'Username',
                                                 'type': 'text'}))
    password = CharField(label="Password",
                         widget=PasswordInput(attrs={'class': 'form-password form-control',
                                                     'placeholder': 'Password',
                                                     'type': 'password'}))


class RegisterUser(ModelForm):
    """
    A form that creates a user, with no privileges, from the given username and
    password.
    """
    error_messages = {
        'password_mismatch': _('Passwords do not match.'),
    }
    password1 = CharField(label=_('Password'),
        widget=PasswordInput)
    password2 = CharField(label=_('Confirm password'),
        widget=PasswordInput,
        help_text=_('Repeat password to confirm.'))
    #captcha = ReCaptchaField(widget=ReCaptchaWidget())

    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name')#, 'captcha')

    def __init__(self, *args, **kwargs):
        super(RegisterUser, self).__init__(*args, **kwargs)

        for key in self.fields:
            self.fields[key].required = True

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise ValidationError(
                self.error_messages['password_mismatch'],
                code='password_mismatch',
            )
        return password2

    def save(self, commit=True):
        user = super(RegisterUser, self).save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user


class NewUserProfileForm(ModelForm):
    class Meta:
        model = Profile
        fields = ['country', ]
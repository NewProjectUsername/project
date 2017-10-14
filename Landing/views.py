import datetime

from django.shortcuts import render, redirect
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.utils.translation import ugettext as _
from django.contrib.auth.forms import UserCreationForm

from Event.models import Event
from Visitor.models import EventProfile
import Event.utils as utils

from .forms import NewUserProfileForm, RegisterUser, EventAuthForm


# Create your views here.

def home(request):
    """Kings landing."""
    context = dict(eventor_yes=False, show_modal=False)

    user_form = RegisterUser()
    profile_form = NewUserProfileForm()
    
    if request.GET.get('register') == 'up':
        context['show_modal'] = True        

    if request.method == 'POST':
        user_form = RegisterUser(request.POST)
        profile_form = NewUserProfileForm(request.POST)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            new_profile = profile_form.save(commit=False)

            email = user_form.cleaned_data.get('email')
            password = user_form.cleaned_data.get('password1')

            user = authenticate(email=email, password=password)
            login(request, user)
            
            profile_form = NewUserProfileForm(request.POST, instance=user.profile)
            if profile_form.is_valid():
                profile_form.save()

            return redirect('home')

        else:
            context['show_modal'] = True
    # Only events that did not start yet are listed (endded events dont show),
    # the first one is the one that will happen the soonest.
    # Uncomment bellow to list all events.
    #also, only events, that are fully registered (registration_step_finished = 7) are shown
    events = Event.objects.filter(
        start_time__gte=datetime.datetime.utcnow(),
        is_public=True,
        registration_step_finished=7
        ).order_by('start_time')[:settings.EVENTS_ON_LANDING]

    #getting event profiles if user is authenticated
    event_profiles = {}
    for e in events:
        if request.user.is_authenticated():
            count =  EventProfile.objects.filter(event=e, user=request.user).count()
            if (count > 0):
                event_profile =  EventProfile.objects.filter(event=e).first()
                event_profiles[e.name] = event_profile

    context['event_profiles'] = event_profiles
    context['events'] = events
    context['user_form'] = user_form
    context['profile_form'] = profile_form


    return render(request, 'Landing/home.html', context)

def event_info(request, event_name):
    """Individual event landing page.""" 
    context = dict(eventor_yes=False)
    event = utils.get_event_by_name_public(request, event_name)
    #this needs to be tested
    if request.user.is_authenticated():
        count =  EventProfile.objects.filter(event=event, user=request.user).count()
        if (count > 0):
            event_profile =  EventProfile.objects.filter(event=event).first()
            context['event_profile'] = event_profile
    context['event'] = event

    return render(request, 'Landing/event_info.html', context)

def event_login(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        user = authenticate(email=email, password=password)
        if user is not None:
            login(request, user)
            if user.has_perm('Event.add_event'):
                try:
                    dest = request.META.get('HTTP_REFERER', '/').split('?')[1].split('=')[1]
                except:
                    dest = 'list_events'
                return redirect(dest)
            if user.has_perm('Event.add_event'):
                return redirect("add_event")
            else:
                return redirect('home')
        else:
            loginForm = EventAuthForm()
            message = _("Username or password is incorrect")
    else:
        print("get")
        loginForm = EventAuthForm()
        try:
            message = request.session.pop('_message')
        except:
            message = ""
    
    context = dict(loginform=loginForm, alert=message, profile_form=NewUserProfileForm())
    return render(request, 'Landing/login.html', context)

# -- Deprecated probably ...
# def event_register(request):
#     """New user registration form."""
#     context = dict()

#     user_form = RegisterUser()
#     profile_form = NewUserProfileForm()

#     if request.method == 'POST':
#         user_form = RegisterUser(request.POST)
#         profile_form = NewUserProfileForm(request.POST)

#         if user_form.is_valid() and profile_form.is_valid():
#             user_form.save()
#             new_profile = profile_form.save(commit=False)

#             email = user_form.cleaned_data.get('email')
#             password = user_form.cleaned_data.get('password1')

#             user = authenticate(email=email, password=password)
#             login(request, user)
            
#             profile_form = NewUserProfileForm(request.POST, instance=user.profile)
#             if profile_form.is_valid():
#                 profile_form.save()

#             return redirect('home')


#     context['user_form'] = user_form
#     context['profile_form'] = profile_form

#     return render(request, 'Landing/register.html', context)

def logout_view(request):
    logout(request)
    return redirect('home')

def search_events_view(request):
    """Search events. doh."""
    context = dict()

    query = request.GET.get('q')

    date = request.GET.get('date')

    # TODO: SQLite nima full text searcha, zato treba to kasneje spedenat.
    events = Event.objects.filter(
        start_time__gte=date,
        is_public=True,
        ).order_by('start_time')[:settings.EVENTS_ON_LANDING]

    # -- Ugly hack.
    events = [event for event in events if query in event.name]

    context['events'] = events
    context['query'] = query

    return render(request, 'Landing/search.html', context)

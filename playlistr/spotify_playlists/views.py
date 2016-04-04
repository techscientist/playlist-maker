from django.core.urlresolvers import reverse
from django.shortcuts import render
from django.shortcuts import redirect
from django.http import HttpResponse
from spotify_playlists.services import API
from playlistr.settings import DEBUG
from os import path
from spotify_playlists.models import User, Party
from django.utils.crypto import get_random_string
from datetime import datetime
import logging

module_dir = path.dirname(__file__)
file_path = path.join(module_dir, "secret.txt")
f = open(file_path, "r")
client_secret = f.readline()
f.close()
api = API(
    "38c7aa7c8b0a4172aa46a5b7833b8454",
    client_secret,
    "user-read-private user-read-email",
    "http://127.0.0.1:8000/redirect"
)

log = logging.getLogger(__name__)


def testing_session(request):
    # Create a session for use in unittests so the test client looks authenticated
    if not DEBUG:
        raise Exception("This view should always be disabled when in production.")
    else:
        log.info("Creating a session for use in testing. id=test_user_id")
        request.session['id'] = 'test_user_id'
        return HttpResponse("Session is created")


def index(request):
    context = {
        "spotify_auth_url": api.get_auth_request_url()
    }
    return render(request, "spotify_playlists/index.html", context=context)


def redirecter(request):
    code = request.GET.get('code')

    if code is None:
        return redirect(reverse('spotify_playlists:index'))

    user = api.get_login_tokens(code)
    profile = api.get_current_user_profile(user['access_token'])
    user['spotify_email'] = profile['email']
    user['id'] = profile['id']
    u = User(**user)
    u.save()
    request.session['id'] = u.id

    try:
        destination = request.session['post_login_url']

    except KeyError:
        # The user just logged in normally, just redirect to logged_in
        return render(request, 'spotify_playlists/logged_in.html')

    else:
        # The user was trying to get somewhere but was not logged in
        del request.session['post_login_url']
        request.session.modified = True
        return redirect(destination)


def join(request, party_id=None):
    try:
        if party_id is None:
            party_id = request.POST.get('party_id')

        user_id = request.session['id']
        party = Party.objects.get(id=party_id)

    except KeyError:
        # User is not logged in, ask them to and then send back here
        request.session['post_login_url'] = reverse('spotify_playlists:join', args=[party_id])
        print(request.session['post_login_url'])
        context = {
            'spotify_auth_url': api.get_auth_request_url()
        }
        return render(request, 'spotify_playlists/log_in.html', context=context)

    except Party.DoesNotExist:
        context = {
            'error_message': "The party you requested could not be found"
        }
        return render(request, 'spotify_playlists/logged_in.html', context=context)

    else:
        user = User.objects.get(id=user_id)

        editable = False
        can_publish = False
        if user is party.creator:
            editable = True
            can_publish = True
        elif user not in party.users.all():
            party.users.add(user)

        party.last_used = datetime.now()
        party.save()

        context = {
            'party': party.get_for_context(request),
            'editable': editable,
            'can_publish': can_publish
        }
        return render(request, 'spotify_playlists/party.html', context=context)


def start(request):
    try:
        user_id = request.session['id']
        party_name = request.POST.get('party_name')

    except KeyError:
        log.info("start view: User with no id in session, or did not choose a party name. redirected to index")
        return redirect('spotify_playlists:index')

    else:
        party_id = get_random_string(length=8)
        log.info("User_id '{}' starting party with name '{}' and party_id '{}' ".format(user_id, party_name, party_id))
        context = {
            "party_name": party_name,
            "party_id": party_id
        }
        return render(request, 'spotify_playlists/start_party.html', context=context)


def save_party(request):
    try:
        user_id = request.session['id']

    except KeyError:
        log.info("save_party view: User with no id in session. redirected to index")
        return redirect('spotify_playlists:index')

    else:
        # Create the party and save in the database
        party_id = get_random_string(8)
        party = Party(
            id=party_id,
            target_no_songs=int(request.POST.get('target_no_songs')),
            last_used=datetime.now(),
            creator=User.objects.get(id=user_id),
            name=request.POST.get('party_name')
        )
        party.save()

        context = {
            'party': party.get_for_context(request),
            'editable': 'true',
            'can_publish': 'true'
        }

        return render(request, 'spotify_playlists/party.html', context=context)


def publish(request):
    try:
        user_id = request.session['id']
        user = User.objects.get(id=user_id)

    except KeyError:
        log.info("publish view: User with no id in session. redirected to index")
        return redirect('spotify_playlists:index')

    except User.DoesNotExist:
        log.warning("publish view: User with session but does not exist, redirected to index")
        return redirect('spotify_playlists:index')

    else:
        party_id = request.GET.get('partyid')
        try:
            party = Party.objects.get(id=party_id)

        except Party.DoesNotExist:
            log.info("publish view: Party requested to be published does not exist, redirected to index")
            return redirect('spotify_playlists:index')

        else:
            if user is not party.creator:
                log.info("publish view: non creator requested publishing of party, redirected to index")
                return redirect('spotify_playlists:index')
            else:
                # Crete the playlist
                return HttpResponse("Not Implemented Yet")


def log_out(request):
    request.session.flush()
    return redirect(reverse('spotify_playlists:index'))

from .models import *
import json
from django.conf import settings
from sensible_audit import audit

log = audit.getLogger(__name__)

def authenticate(request):
	token = request.REQUEST.get('access_token')
	host = request.META['REMOTE_ADDR']
	if not host in settings.PLATFORM['ip_addr']: 
		log.error({'response': json.dumps({'error': 'ip address not authorized '+host})})
		return {'error': 'ip address not authorized', 'response': json.dumps({'error': 'ip address not authorized '+host})}

	try: user = PlatformAccessToken.objects.get(token=token).user
        except PlatformAccessToken.DoesNotExist: return {'error': 'user not found', 'response': json.dumps({'error': 'user not found'})}

	return {'ok':'authenticated', 'user': user}


def authenticatePlatform(request):
	host = request.META['REMOTE_ADDR']
	if not host in settings.PLATFORM['ip_addr']: return {'error': 'ip address not authorized', 'response': json.dumps({'error': 'ip address not authorized '+host})}
	return {'ok':'platform calling'}

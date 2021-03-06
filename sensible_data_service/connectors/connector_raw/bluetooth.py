from django.http import HttpResponse
import bson.json_util as json
from authorization_manager import authorization_manager
from utils import database
from django.shortcuts import render_to_response
from accounts.models import UserRole
from django.contrib.auth.models import User
import re
import urllib
import time
from connector_utils import *
from sensible_audit import audit

log = audit.getLogger(__name__)

def bluetooth(request):
	decrypted = booleanize(request.REQUEST.get('decrypted', False))

	if decrypted:
		accepted_scopes = set(['connector_raw.bluetooth', 'connector_raw.all_data'])
	else:
		accepted_scopes = set(['connector_raw.bluetooth', 'connector_raw.all_data', 'connector_raw.all_data_researcher'])

	auth = authorization_manager.authenticate_token(request)

	if 'error' in auth:
		response = {'meta':{'status':{'status':'error','code':401,'desc':auth['error']}}}
		log.error(audit.message(request, response))
		return HttpResponse(json.dumps(response), status=401, content_type="application/json")

	auth_scopes = set([x for x in auth['scope']])

	if len(accepted_scopes & auth_scopes) == 0:
		response = {'meta':{'status':{'status':'error','code':401,'desc':'token not authorized for any accepted scope %s'%str(list(accepted_scopes))}}}
		log.error(audit.message(request, response))
		return HttpResponse(json.dumps(response), status=401)
	
	if ('dummy' in request.REQUEST.keys()):
		return HttpResponse('[]', content_type="application/json")

	is_researcher = False
	for s in auth_scopes:
		if s == 'connector_raw.all_data_researcher': is_researcher = True
	
	users_to_return = buildUsersToReturn(auth['user'], request, is_researcher = is_researcher)
	#return HttpResponse(str((users_to_return)) + ', ' + str(is_researcher))
	roles = []
	try: roles = [x.role for x in UserRole.objects.get(user=auth['user']).roles.all()]
	except: pass

	own_data = False
	if len(users_to_return) == 1 and users_to_return[0] == auth['user'].username: own_data = True

	return bluetoothBuild(request, users_to_return, decrypted = decrypted, own_data = own_data, roles = roles)

def bluetoothBuild(request, users_to_return, decrypted = False, own_data = False, roles = []):
	_start_time = time.time()
	
	pretty = booleanize(request.REQUEST.get('pretty', False))
	results = None
	query = None
	proc_req = None
	response = {}
	response['meta'] = {}

	try:
		if len(users_to_return) == 0:
			raise BadRequestException('error',403,'The current token does not allow to view data from any users')
		proc_req = processApiCall(request, users_to_return)
		query = buildQuery(users_to_return, proc_req)	
		collection = 'edu_mit_media_funf_probe_builtin_BluetoothProbe'
		if own_data and 'researcher' in roles: collection += '_researcher'

		db = database.Database()
		
		docs = db.getDocumentsCustom(query=query, collection=collection,\
				fields = proc_req['fields'])

		### hinting
		# if the users are specified, we use the hint with users
		if proc_req['users'] is not None:
			docs = docs.hint([('data.TIMESTAMP',proc_req['order']), ('_id',1), ('user',1)])
		# else, we use only id and timestamp
		else:
			docs = docs.hint([('data.TIMESTAMP',proc_req['order']), ('_id',1)])
		#pagination (skipping)
		if proc_req['after'] is not None:
			docs = docs.skip(1)

		#apply limit
		docs.limit(proc_req['limit'])

		try:
			results = cursorToArray(docs)
		except Exception as e:
			raise BadRequestException('error',500,'The request caused a DB malfunction: ' + str(e))
		results_count = len(results)

		response['meta']['status'] = proc_req['status']
		response['meta']['results_count'] = len(results)
		response['meta']['api_call'] = request.REQUEST
		response['meta']['query'] = query
		response['results'] = results

		if len(results) > 0:
			response['meta']['paging'] = {}
			response['meta']['paging']['cursors'] = {}
			response['meta']['paging']['cursors']['after'] =\
					{proc_req['sortby']:getValueOfFullKey(results[-1], proc_req['sortby']),\
					'_id':results[-1]['_id'],
					'user':results[-1]['user']}
			if results_count == proc_req['limit']:
				if proc_req['after'] is not None:	
					response['meta']['paging']['links'] =\
						{'next':re.sub('&after=[^ &]+','&after=' + urlize_dict(response['meta']['paging']['cursors']['after']),request.build_absolute_uri())}
				else:
					response['meta']['paging']['links'] = \
						{'next':request.build_absolute_uri() + '&after=' + urlize_dict(response['meta']['paging']['cursors']['after'])}
	except BadRequestException as e:
		response['meta']['status'] = e.value
	
	response['meta']['execution_time_seconds'] = time.time()-_start_time
	callback = request.REQUEST.get('callback','')

	if len(callback) > 0:
		data = '%s(%s);' % (callback, json.dumps(response))
		return HttpResponse(data, content_type="text/javascript", status=response['meta']['status']['code'])

	if decrypted:
		pass

	if pretty:
		log.info(audit.message(request, response['meta']['api_call']))
		return render_to_response('pretty_json.html', {'response': json.dumps(response, indent=2)})
	else:
		log.info(audit.message(request, response['meta']['api_call']))
		return HttpResponse(json.dumps(response), content_type="application/json", status=response['meta']['status']['code'])
	return HttpResponse('hello decrypted')

def urlize_dict(dictionary):
	return urllib.quote(json.dumps(dictionary, indent=None, separators=(',',':')))


def cursorToArray(cursor):
	return [doc for doc in cursor]

def buildUsersToReturn(auth_user, request, is_researcher = False):
	users_to_return = []
	if not is_researcher:
		users_to_return.append(auth_user.username)
		return users_to_return
	
	if is_researcher:
		requested_users = [user for user in request.REQUEST.get('users','').split(',') if len(user) > 0]
		if len(requested_users) > 0:
			users_to_return = requested_users
		else: users_to_return.append('all')
		return users_to_return
	return users_to_return

def processApiCall(request, users_to_return):
	
	response = {}
	api_params = ['bearer_token','pretty','decrypted','order','fields','start_date','end_date','limit','users','after','callback']
	for k in request.REQUEST.keys():
		if k not in api_params:
			raise BadRequestException('error',400, str(k) + ' is not a legal API parameter.'\
					+' Legal API parameters are: ' + ', '.join(api_params))

	response['status'] = {'status':'OK','code':200, 'desc':''}
	response['fields'] = None
	response['sortby'] = None
	response['order'] = None
	response['start_date'] = None
	response['end_date'] = None
	response['limit'] = 1000
	response['users'] = None
	response['after'] = None

	### deal with sorting
	# sorting will be supported later. Now, we can only sort by data.TIMESTAMP, either asc or desc
	response['sortby'] = 'data.TIMESTAMP'
	if request.REQUEST.get('order', None) is not None:
		if request.REQUEST.get('order',None) not in ['-1','1']:
			raise BadRequestException('error',400,str(request.REQUEST.get('order')) + ' is not a valid value for order parameter. Use 1 for ascending or -1 for descending')
		else:
			response['order'] = int(request.REQUEST.get('order'))
	else:
		response['order'] = -1
	
	### deal with fields
	fields_string = request.REQUEST.get('fields', '')
	if len(fields_string) > 0:
		response['fields'] = {\
                                'user':1,\
                                'data.TIMESTAMP':1,\
                                '_id':1}
		for field in fields_string.split(','):
			if len(field) > 0 and field != 'sensible_token':
				response['fields'][field] = 1
	# default set of fields
	else:
		response['fields'] = {\
				'user':1,\
				'data.TIMESTAMP':1,\
				'_id':1,\
				'data.DEVICES':1}
	# always add the field by which sorting is done
	#if response['sortby'] not in response['fields'].keys():
	#	response['fields'][response['sortby']] = 1

		
	### deal with start_date and end_date
	if request.REQUEST.get('start_date',None) is not None:
		try:
			response['start_date'] = int(request.REQUEST.get('start_date'))
		except ValueError:
			raise BadRequestException('error',400,request.REQUEST.get('start_date') + ' is not a valid value for the start_date parameter. Use an integer value')
	if request.REQUEST.get('end_date',None) is not None:
		try:
			response['end_date'] = int(request.REQUEST.get('end_date'))
		except:
			raise BadRequestException('error',400,request.REQUEST.get('end_date') + ' is not a valid value for the end_date parameter. Use an integer value')

	### deal with limit
	if int(request.REQUEST.get('limit',1000)) < 1000:
		try:
			response['limit'] = int(request.REQUEST.get('limit'))
		except ValueError:
			raise BadRequestException('error',400, request.REQUEST.get('limit') + ' is not a valid value for the limit parameter. Use an integer value')
	
	# list of users is passed as function argument	
	response['users'] = users_to_return
	
	### deal with after (paging)
	if request.REQUEST.get('after', None) is not None:
		try:
			response['after'] = json.loads(request.REQUEST.get('after', None))
		except ValueError:
			raise BadRequestException('error',400,'Specified after parameter is not a valid JSON string')

	### return
	return response


def buildQuery(users_to_return, request):
	query = {'$query':{}}
	if not 'all' in users_to_return:
		query['$query']['user'] = {'$in':users_to_return}
	

	
	if request['after'] is not None: # there is paging involved
		#if request['order']==1:
		query['$min'] = request['after']
		#else:
		#	query['$max'] = request['after']

	
	if request['end_date'] is not None or request['start_date'] is not None:
		query['$query']['data.TIMESTAMP'] = {}
		if request['end_date'] is not None:
			query['$query']['data.TIMESTAMP']['$lte'] = request['end_date']
		if request['start_date'] is not None:
			query['$query']['data.TIMESTAMP']['$gte'] = request['start_date']
		
	return query



def getValueOfFullKey(dictionary, fullkey):
	result = dictionary
	for key in fullkey.split('.'):
		result = result[key]
	return result

class BadRequestException(Exception):
	def __init__(self, value):
		self.value = value
	
	def __init__(self, status, code, description):
		self.value = {}
		self.value['status'] = status
		self.value['code'] = code
		self.value['desc'] = description
	
	def __str__(self):
		return repr(self.value)

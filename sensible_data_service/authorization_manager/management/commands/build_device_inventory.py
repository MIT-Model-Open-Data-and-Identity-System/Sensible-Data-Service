from django.core.management.base import NoArgsCommand
from authorization_manager.models import Authorization
from application_manager.models import Application
from collections import defaultdict
from anonymizer import anonymizer
from utils import database

class Command(NoArgsCommand):
	def handle_noargs(self, **options):
		anonymizerObject = anonymizer.Anonymizer()
		db = database.Database()

		authorizations = Authorization.objects.filter(application=Application.objects.get(name="Phone Data Collector"))
		print len(authorizations)
		devices = defaultdict(lambda: defaultdict(str))
		for a in authorizations:
			try: devices[a.device.device_id][a.activated_at] = a.user.username
			except: print a.device, a.user.username


		mapping = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: 9999999999999)))
		for d in devices:
			users = defaultdict(lambda: 9999999999999)
			timestamps = defaultdict(str)
			for t in devices[d]:
				if users[devices[d][t]] > t:
					users[devices[d][t]] = t
					
			for u in users:
				timestamps[users[u]] = u
			
			previous_t = -1
			for t in sorted(timestamps, reverse=True):
				mapping[d][timestamps[t]]['start'] = t
				if not previous_t == -1: 
					mapping[d][timestamps[t]]['end'] = previous_t
				else:
					mapping[d][timestamps[t]]['end'] = 9999999999999
				previous_t = t

		for device_id in mapping:
			for u in mapping[device_id]:
				a_device_id = anonymizerObject.anonymizeValue('device_id', device_id)
				hardware_info = None
				try: 
#					hardware_info = db.getDocuments(query={'device_id':a_device_id}, collection='edu_mit_media_funf_probe_builtin_HardwareInfoProbe')[0]
					for v in db.getDocuments(query={'device_id':a_device_id}, collection='edu_mit_media_funf_probe_builtin_HardwareInfoProbe').sort('timestamp', -1):
						if v['timestamp_added'] < v['timestamp']: continue
						hardware_info = v
						break

				except: 
					continue
				if not hardware_info: continue
				doc = {}
				doc['_id'] = a_device_id + '_' + u
				doc['device_id'] = device_id
				doc['a_device_id'] = a_device_id
				doc['user'] = u
				doc['start'] = mapping[device_id][u]['start']
				doc['end'] = mapping[device_id][u]['end']
				doc['bt_mac'] = hardware_info['device_bt_mac']
				doc['a_bt_mac'] = hardware_info['data']['BLUETOOTH_MAC']
				doc['a_wifi_mac'] = hardware_info['data']['WIFI_MAC']
				doc['sensible_version'] = hardware_info['uuid'].split('-')[-2]
				doc['funf_version'] = hardware_info['uuid'].split('-')[-1]

				collection = 'device_inventory'
				(db.getDatabase(collection))[collection].update(spec={'_id':doc['_id']}, document=doc, upsert=True)


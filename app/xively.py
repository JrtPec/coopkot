from flask import flash
import requests, json
from werkzeug.security import safe_join
API_URL = 'https://api.xively.com/v2/feeds/'

def get_datastreams(feed):
	headers = {'X-ApiKey': feed.api_key}
	url = safe_join(API_URL, str(feed.xively_id))
	try:
		r = requests.get(url,headers=headers)
		decoded_data = r.json()
	except Exception, e:
		flash('Xively request failed')
		response = 'error'
		return response

	if 'datastreams' in decoded_data:
		datastreams = decoded_data['datastreams']
		return datastreams
	else:
		flash('No datastreams decoded')
		response = 'error'
		return response

def get_dataset(datastream):
	headers = {'X-ApiKey': datastream.feed.api_key}
	url = safe_join(API_URL, str(datastream.feed.xively_id))
	url = url + '/datastreams/'
	url = safe_join(url,datastream.xively_id)
	url = url + '.json?duration=12hours&interval=60&function=average'
	try:
		r = requests.get(url,headers=headers)
		decoded_data = r.text
		return decoded_data
	except Exception, e:
		flash('Xively request failed')
		response = 'error'
		return False


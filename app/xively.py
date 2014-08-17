from flask import flash
import requests, json
from werkzeug.security import safe_join
API_URL = 'https://api.xively.com/v2/feeds/'

zoom = [{'duration':'1year','interval':'86400'},
	{'duration':'6months','interval':'86400'},
	{'duration':'90days','interval':'2600000'},
	{'duration':'31days','interval':'86400'},
	{'duration':'14days','interval':'86400'},
	{'duration':'5days','interval':'86400'},
	{'duration':'24hours','interval':'4320'},
	{'duration':'12hours','interval':'2160'},
	{'duration':'6hours','interval':'1080'},
	{'duration':'3hours','interval':'540'},
	{'duration':'1hours','interval':'180'},
	{'duration':'30minutes','interval':'90'},
	{'duration':'15minutes','interval':'45'},
	{'duration':'7minutes','interval':'21'}]

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

def get_dataset(datastream, zoom_level, timeStamp):
	headers = {'X-ApiKey': datastream.feed.api_key}
	url = safe_join(API_URL, str(datastream.feed.xively_id))
	url = url + '/datastreams/'
	url = safe_join(url,datastream.xively_id)
	url = url + '.json?duration=' + zoom[zoom_level]['duration']
	url = url + '&interval=' + zoom[zoom_level]['interval']
	url = url + '&function=average&find_previous'
	if timeStamp != None:
		url = url + '&end=' + timeStamp
	try:
		r = requests.get(url,headers=headers)
		decoded_data = r.text
		decoded_data = json.loads(decoded_data)
		decoded_data.update({'zoom_level':zoom_level})
		decoded_data = json.dumps(decoded_data)
		return decoded_data
	except Exception, e:
		flash('Xively request failed')
		response = 'error'
		return False


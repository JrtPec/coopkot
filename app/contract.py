from xively import get_datapoint
from datetime import date, datetime, timedelta

def nextMonth(date):
	if date.month < 12:
		next = date.replace(date.year,date.month+1,1)
	else:
		next = date.replace(date.year+1,1,1)
	return next

class Usage(dict):
    def __init__(self,datastream,value):
        self.datastream = datastream
        self.shared = datastream.rooms.count()
        if datastream.type != 2:
        	self.total_value = round(value/1000,2)
        else:
        	self.total_value = round(value,2)
        self.value = round(self.total_value/self.shared,2)

class Month(dict):
    def __init__(self,start_date,end_date,usages,prices):
        self.start_date = start_date
        self.end_date = end_date
        self.usages = usages
        self.total_e = 0.0
        self.total_h = 0.0
        self.total_w = 0.0
        for usage in self.usages:
        	if usage.datastream.type == 0:
        		self.total_e += usage.value
        	elif usage.datastream.type == 1:
        		self.total_h += usage.value
        	elif usage.datastream.type == 2:
        		self.total_w += usage.value
        self.cost_e = round(self.total_e * prices.electricity/100,2)
        self.cost_h = round(self.total_h * prices.heat/100,2)
        self.cost_w = round(self.total_w * prices.water/100,2)
        self.cost_total = self.cost_e + self.cost_h + self.cost_w

def get_usage_per_month(datastreams, start, end, property):
	months = []
	if start.date() > date.today():
		return months
	start_temp = start.date()
	start_values = []
	for datastream in datastreams:
		start_values.append(get_datapoint(datastream=datastream,timestamp=start_temp))
	
	while True:
		end_temp = min(date.today(),end.date(),nextMonth(start_temp))
		end_values = []
		for datastream in datastreams:
			end_values.append(get_datapoint(datastream=datastream,timestamp=end_temp))

		usages = []
		for i in xrange(len(end_values)):
			usages.append(Usage(datastream=datastreams[i],value=(end_values[i] - start_values[i])))

		print start_temp
		print end_temp	
		print property.get_historical_prices(timestamp=start_temp).electricity
		months.append(Month(start_date=start_temp,end_date=end_temp,usages=usages,prices=property.get_historical_prices(timestamp=start_temp)))

		if end_temp == date.today() or end_temp == end.date():
			break
		else:
			start_temp = end_temp
			start_values = end_values
	return months

def get_last_week(datastreams,property):
	total = 0
	for datastream in datastreams:
		end_value = get_datapoint(datastream=datastream,timestamp=datetime.utcnow())
		start_value = get_datapoint(datastream=datastream,timestamp=datetime.utcnow()-timedelta(weeks=1))
		usage = end_value - start_value
		total = total + usage
	return total

def get_last_month(datastreams,property):
	total = 0
	for datastream in datastreams:
		end_value = get_datapoint(datastream=datastream,timestamp=datetime.utcnow())
		start_value = get_datapoint(datastream=datastream,timestamp=datetime.utcnow()-timedelta(weeks=4))
		usage = end_value - start_value
		total = total + usage
	return total

def get_last_year(datastreams,property):
	total = 0
	for datastream in datastreams:
		end_value = get_datapoint(datastream=datastream,timestamp=datetime.utcnow())
		start_value = get_datapoint(datastream=datastream,timestamp=datetime.utcnow()-timedelta(weeks=52))
		usage = end_value - start_value
		total = total + usage
	return total
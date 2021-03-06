from flask import Flask, jsonify, request,abort
from flask_restplus import Resource, Api, reqparse
import requests
import json
import time
from datetime import datetime, timedelta
app = Flask(__name__)
api = Api()
api.init_app(app)



@api.route('/')
class HelloWorld(Resource):
	def get():
	    return 'Hello, World!'
	    
 

def getimage(place):
	url = 'https://maps.googleapis.com/maps/api/place/textsearch/json?key=AIzaSyDb1uML_5xvDqtQCWppi0z8MSy5YpN7zvU&input={}&inputtype=text'.format(place)
	resp = requests.get(url = url)
	data = resp.json()
	photo = 'https://via.placeholder.com/340'
	if ( len(data['results']) > 0):
		photo = data['results'][0]['photos'][0]
		photo = 'https://maps.googleapis.com/maps/api/place/photo?maxwidth=400&photoreference=' + photo['photo_reference'] + '&key=AIzaSyDb1uML_5xvDqtQCWppi0z8MSy5YpN7zvU'
	return photo



def getCity(latlng):
	url = 'https://maps.googleapis.com/maps/api/geocode/json?key=AIzaSyDb1uML_5xvDqtQCWppi0z8MSy5YpN7zvU&latlng={}'.format(latlng)
	resp = requests.get(url = url)
	data = resp.json()
	if( 'OK' in data['status'] ):
		print(data['results'][0]['address_components'])
		return data['results'][0]['address_components'][ min(len(data['results'][0]['address_components']) -3, 3) ]['long_name']
	return ''

def cityCode(text):
	url = 'http://partners.api.skyscanner.net/apiservices/autosuggest/v1.0/GB/eur/en-US?query={}&apiKey=ha796565994483997905142768862425'.format(text)
	resp = requests.get(url = url)
	data = resp.json()
	places = data['Places']
	if(len(places) > 0):
		return places[0]["CityId"]
	return text


parser = reqparse.RequestParser()
parser.add_argument('city', type=str, help='Location not found', location='args')
parser.add_argument('latlng', type=str, help='Location not provided', location='args')
parser.add_argument('page', type=int,location='args')

def getWeekends():
	print(datetime.today().day)
	weekno = datetime.today().weekday()
	print(weekno)
	next_friday = datetime.today() + timedelta(days = 4 - weekno if weekno < 4 else 11 - weekno )
	weekends = [next_friday]
	for i in range(3):
		weekends.append( next_friday + timedelta(days = 7) )
		next_friday = next_friday + timedelta(days = 7) 
	# print(weekends)
	return weekends

@api.route('/quotes')
class RoutesApi(Resource):
	def get(self):
			args = parser.parse_args()
			page = 0
			if 'page' in request.args:
				page = args['page']
			
			if('latlng' in request.args):
				city = cityCode(getCity(args['latlng']))
				
			else:
				city = cityCode(args['city'])
				
			print (city)
			weekends = getWeekends()
			result = []
			places = dict()
			for weekend in weekends:
				url = 'http://partners.api.skyscanner.net/apiservices/browsequotes/v1.0/GB/eur/en-US/' + city + '/anywhere/' + weekend.strftime("%Y%m%d") + '/'+ (weekend + timedelta(days=2)).strftime("%Y%m%d") +'?apikey=ha796565994483997905142768862425&direct=true'
				
				resp = requests.get(url=url)
				data = resp.json()
				if 'Places' in data.keys():
					for v in data['Places'] :
						places[v['PlaceId']] = v
					
					direct = [ x for x in data['Quotes'] if x['Direct'] == True  ]
					
					
					
					for u in direct:
						a = dict()
						a['MinPrice'] = u['MinPrice']
						a['From'] = places[u['OutboundLeg']['OriginId']]['CityName']
						a['FromCode'] = places[u['OutboundLeg']['OriginId']]['CityId'] + '-sky'
						a['To'] = places[u['InboundLeg']['OriginId']]['CityName']
						a['ToCode'] = places[u['InboundLeg']['OriginId']]['CityId'] + '-sky'
						a['Photo'] = getimage(a['To'])
						d1 = datetime.strptime(u['OutboundLeg']['DepartureDate'], '%Y-%m-%dT%H:%M:%S')
						d2 = datetime.strptime(u['InboundLeg']['DepartureDate'], '%Y-%m-%dT%H:%M:%S')
						a['departure'] = d1.strftime("%Y-%m-%d")
						a['arrival']  = d2.strftime("%Y-%m-%d")
						a['date'] = "{}-{} {}".format(d1.day, d2.day, d1.strftime("%b"))
						result.append(a)
					
			from operator import itemgetter
			new_result = sorted(result,  key=lambda k: k['MinPrice'])
			
			
			return jsonify(new_result[page*10: min(len(new_result), (page+1)*10 )] )
			
			


@api.route('/route/<origin>/<destination>/<outbound>/<inbound>')
class SingleRouteApi(Resource):
	def get(self,origin, destination, outbound, inbound):
		url = 'http://partners.api.skyscanner.net/apiservices/browseroutes/v1.0/GB/eur/en-US/{}/{}/{}/{}?apikey=ha796565994483997905142768862425&direct=true'.format(origin, destination, outbound, inbound)
		print(url)
		# data = dict(country = 'GB',
		# 	locale = 'en-US',
		# 	currency = 'eur',
		# 	apikey  = 'ha796565994483997905142768862425',
		# 	originPlace = origin,
		# 	destinationPlace = destination,
		# 	OutboundDate = outbound,
		# 	InboundDate = inbound)
		# headers = {'content-type': 'application/x-www-form-urlencoded'}
		resp = requests.get(url = url)
		# print(resp.headers)
		# if 'Location' not in resp.headers:
		# 	abort(405)
		# location = resp.headers['Location'] + '?apikey=ha796565994483997905142768862425&sortType=price&sortOrder=asc&stops=0'
		# next_resp = requests.get(location)
		result = resp.json() 
		# while( 'UpdatesComplete' not in result['Status']  ):
		# 	next_resp = requests.get(location)
		# 	result = next_resp.json() 
		# 	print(result['Status'] )
		# 	time.sleep(10)
		
		
		places = dict()
		if 'Places' in result.keys():
					for v in result['Places'] :
						places[v['PlaceId']] = v
		
		min_price = 1000000
		min_quote = {}
		for u in result['Quotes']:
			if( u['MinPrice'] < min_price):
				min_price = u['MinPrice']
				min_quote = u
		
		u['from'] = places[u['InboundLeg']['OriginId']]['CityName']
		
		return jsonify(min_quote)
			
if __name__ == "__main__":
    app.run( port=8080, host='0.0.0.0', debug=True)
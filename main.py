# Copyright 2015 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# [START app]
import os

import jinja2
import webapp2

import pprint
import urllib
import json
from google.appengine.api import urlfetch

from jinja2 import Template

gmap_api_key = "AIzaSyA5Dzn2jYutVPBJDAEEqoM1ziEbx0_7ra8"

# you can set key as config
# app.config['GOOGLEMAPS_KEY'] = gmap_api_key

# Initialize the extension
# GoogleMaps(app)

# you can also pass the key here if you prefer
# GoogleMaps(app, key=gmap_api_key)

instagram_api_key = "57c1878e21fe4873a4f5c63bfb9fadd9"
instagram_code = "478d1b3ee3284e27bdce3867e0728db9"
instagram_access_token = "461138458.57c1878.cf3bc878f3e540bb8b20d2731a79829c"
ig_access_token = "461138458.57c1878.cf3bc878f3e540bb8b20d2731a79829c"
url = "https://maps.googleapis.com/maps/api/geocode/json?address=Melbourne,%20Ca&key=" + gmap_api_key

API_KEY = "oHWGmS9qe52xHO_NO172Ys_Pv4XUeDa6W67tJrrOdO8fyhsk9MWGF58UXlkAWdRm1ZIHu8jbgAJIqP2VBlVloC5oHuB-_9sYpX7D0eeOzIgIyLCFa5osmBh3GA5QXHYx"
CLIENT_ID = "PnGEWHTDG0jfx_ch-wj0gw"

API_HOST = 'https://api.yelp.com'
SEARCH_PATH = '/v3/businesses/search'
BUSINESS_PATH = '/v3/businesses/'

DEFAULT_TERM = 'nightclubs'
DEFAULT_LOCATION = 'Melbourne'
SEARCH_LIMIT = 10

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)


def request_id(host, path, api_key, term, location, limit):
    url = '{0}{1}'.format(host, urllib.quote(path.encode('utf8')))
    headers = {
        'Authorization': 'Bearer %s' % api_key,
    }
    url = url +"?term=" + term + "&location="+location
    response = urlfetch.fetch(url, headers=headers)
    j = json.loads(response.content)
    return j

def request_reviews(host, path, api_key):
    url = '{0}{1}'.format(host, urllib.quote(path.encode('utf8')))
    headers = {
        'Authorization': 'Bearer %s' % api_key,
    }
    response = urlfetch.fetch(url, headers=headers)
    j = json.loads(response.content)
    return j


def search(api_key, term, location):
    term = term.replace(' ', '+')
    location = location.replace(' ', '+')
    limit = SEARCH_LIMIT
    return request_id(API_HOST, SEARCH_PATH, api_key, term, location, limit)


def get_business(api_key, business_id):
    business_path = BUSINESS_PATH + business_id + "/reviews"
    return request_reviews(API_HOST, business_path, api_key)


def query_api(term, location):
    response = search(API_KEY, term, location)
    print response
    businesses = response.get('businesses')
    if not businesses:
        print(u'No businesses for {0} in {1} found.'.format(term, location))
        return

    business_id = businesses[0]['id']
    print(u'{0} businesses found, querying business info ' \
          'for the top result "{1}" ...'.format(
        len(businesses), business_id))
    response = get_business(API_KEY, business_id)
    print(u'Result for business "{0}" found:'.format(business_id))
    pprint.pprint(response, indent=2)


def fetch_reviews():
    query_api(DEFAULT_TERM, DEFAULT_LOCATION)


class MainPage(webapp2.RequestHandler):
    def get(self):
        fetch_reviews()
        self.response.headers['Content-Type'] = 'text/html'
        res = urlfetch.fetch(url)
        response_json = res.content
        template = JINJA_ENVIRONMENT.get_template('index.html')
        self.response.write(template.render({}))

app = webapp2.WSGIApplication([
    ('/', MainPage),
], debug=True)

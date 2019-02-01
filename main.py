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

import cloudstorage as gcs
from google.appengine.api import app_identity

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
# url = "https://maps.googleapis.com/maps/api/geocode/json?address=Melbourne,%20Ca&key=" + gmap_api_key

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

gcs.set_default_retry_params(gcs.RetryParams(initial_delay=0.2,
                                             max_delay=5.0,
                                             backoff_factor=2,
                                             max_retry_period=15))


def request_id(host, path, api_key, term, location, limit):
    url = '{0}{1}'.format(host, urllib.quote(path.encode('utf8')))
    headers = {
        'Authorization': 'Bearer %s' % api_key,
    }
    url = url + "?term=" + term + "&location=" + location
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
    # print response
    businesses = response.get('businesses')
    if not businesses:
        print(u'No businesses for {0} in {1} found.'.format(term, location))
        return

    business_id = businesses[0]['id']
    print(u'{0} businesses found, querying business info ' \
          'for the top result "{1}" ...'.format(
        len(businesses), business_id))

    bucket_name = os.environ.get('BUCKET_NAME',
                                 app_identity.get_default_gcs_bucket_name())

    write_retry_params = gcs.RetryParams(backoff_factor=1.1)

    bucket = '/' + "nightclubs"
    filename = bucket + '/nightclubsdata.txt'

    gcs_file = gcs.open(filename,
                        'w',
                        content_type='text/plain',
                        options={'x-goog-meta-foo': 'foo',
                                 'x-goog-meta-bar': 'bar'},
                        retry_params=write_retry_params)

    total_data = []
    for bus in businesses:
        data = []
        data.append(bus['name'])
        data.append(bus['coordinates']['latitude'])
        data.append(bus['coordinates']['longitude'])
        res = get_business(API_KEY, bus['id'])
        total_rating = 0
        total_count = 0;
        for r in res['reviews']:
            total_rating += r['rating']
            total_count += 1
        if total_count > 0:
            avg_rating = total_rating / total_count
            data.append(avg_rating)
        else:
            data.append(0)
        total_data.append(data)
        gcs_file.write(json.dumps(res))

    total_data.sort(key=lambda x: x[3], reverse=True)
    return total_data[0:min(5, len(total_data))]


def fetch_reviews():
    result = query_api(DEFAULT_TERM, DEFAULT_LOCATION)
    return result


class MainPage(webapp2.RequestHandler):
    def get(self):
        result = fetch_reviews()
        self.response.headers['Content-Type'] = 'text/html'
        template = JINJA_ENVIRONMENT.get_template('index.html')

        map_url = """
        https://maps.googleapis.com/maps/api/staticmap?center=-37.8136,144.9631&zoom=10&size=800x600
        &maptype=roadmap
        """
        for r in result:
            map_url += "&markers=label:" + str(r[0]) + str(r[1]) + "," + str(r[2])
        map_url += "&key=AIzaSyA5Dzn2jYutVPBJDAEEqoM1ziEbx0_7ra8"
        values = {'results': result, 'url': map_url}
        print values
        # self.response.write(template.render(values))

        text_to_render = """
        <!DOCTYPE html>
        <html>
        <body>
        <h1>Top 5 Nightclubs in Melbourne</h1>

        <div id="googleMap" style="width:70%;height:400px; float: left"></div>
        <div id="content" style="text-align: center;width:30%;height:400px; float: left; background:#ff7892a1;  float: left">
        """

        for r in result:
            text_to_render += '<div align="center" style="font-size:24px;padding:10px;color:white;">'
            text_to_render += str(r[0]) + '</div><br>'

        text_to_render += """
        </div>


        <script type="text/javascript">

        function initMap() {
        var mapProp= {
          center:new google.maps.LatLng(-37.8136, 144.9631),
          zoom:13,
        };

        var map = new google.maps.Map(document.getElementById("googleMap"), mapProp);
                          var point = {lat: -37.826668, lng: 144.945793 };
                          var marker = new google.maps.Marker({
                            position: point,
                            map: map,
                            label: 'Neverland Entertainment'
                        });
        """

        for r in result:
            text_to_render += "\nvar point = new google.maps.LatLng(" + str(r[1]) + "," + str(r[2]) + ");"
            text_to_render += """\nvar marker = new google.maps.Marker({position: point,
                                                        map: map,
                                                        """
            text_to_render += "\nlabel: '" + r[0] + "'});"

        text_to_render += """
        }
        </script>
        <script src="https://maps.googleapis.com/maps/api/js?key=AIzaSyA5Dzn2jYutVPBJDAEEqoM1ziEbx0_7ra8&callback=initMap"></script>
        </body>
        </html>
        """
        self.response.write(text_to_render)


app = webapp2.WSGIApplication([
    ('/', MainPage),
], debug=True)

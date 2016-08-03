#!/usr/bin/env python

from __future__ import print_function
from ciscosparkapi import CiscoSparkAPI
import datetime
#from dateutil import parser


# we need to know our token
TOKEN = 'my-lengthy-spark-token-here'
NAME = 'my-test-room-name-here'

# initialize the API
spark = CiscoSparkAPI(access_token=TOKEN)

# find a 'group' room with the given NAME
for room in spark.rooms.list(type='group'):
    if room.title == NAME:
        print(room.dumps())
        break

# create a message in that room
message = spark.messages.create(room.id, text='hello')
print(message.dumps())


# define a callback in case we get throttled
def cb(sleep_time):
    print('we should sleep (%d)' % sleep_time)
    sleep(sleep_time)
    return True

# pass the callback into the API
spark.session.ratelimit_callback = cb

# create a lot of users in the room from above
for m in 100 * ['me@home.net', 'user@somewhere.com', 'santa@northpole.org']:
    try:
        spark.memberships.create(room.id, personEmail=m)
    except ciscosparkapi.exceptions.SparkApiError, e:
        if spark.session.last_response.status_code == 409:
            print('user already in room!')
        else:
            print(e)
            break
    print('.')

# this needs to go into the restsession, i guess
spark.session.ratelimit_callback = cb

#cursor = parser.parse('2015-10-01 16:41:20.629000')
cursor = datetime.datetime.utcnow()

while cursor > room.created:
    print(80*"*")
    counter = 0
    for message in spark.messages.list(room.id, before=cursor):
        print('%s: %s <%s>' % (str(message.created), spark.people.details(message.personId), message.text))
        counter =+ 1
    if counter > 0:
        cursor = message.created
    else:
        cursor = room.created


print(json.dumps(dict(spark.session.last_response.headers), indent=4))


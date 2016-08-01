#!/usr/bin/env python

from __future__ import print_function
from ciscosparkapi import CiscoSparkAPI


# we need to know our token
TOKEN = 'my-lengthy-spark-token-here'
NAME = 'my-test-room-name-here'

spark = CiscoSparkAPI(access_token=TOKEN)
for room in spark.rooms.list(type='group'):
    if room.title == NAME:
        print(room.dumps())
        break

message = spark.messages.create(room.id, text='hello')
print(message.dumps())


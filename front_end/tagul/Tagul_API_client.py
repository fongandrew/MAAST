#!/usr/bin/env python3
import xmlrpclib
import zlib

#create XML-RPC client instance connected to Tagul
xmlrpcClient = xmlrpclib.ServerProxy('https://tagul.com:4433/api')

#read cloudAPI.xml file
with open('cloudAPI.xml', "r") as file:
	cloudAPIxml = file.read()

#get svgz cloud from Tagul
cloud = xmlrpcClient.generateCloud (
	{
		'userName': 'monica@ischool.berkeley.edu',
		'apiKey': 'leeHaiva3ahFoo2oothaePohn'
	},
	cloudAPIxml
)

#save the compressed cloud
with open('myCloud.svgz', 'wb') as file:
	file.write(cloud.data)

#uncomment this to save decompressed svg cloud
with open('myCloud.svg', 'wb') as file:
	file.write(zlib.decompress(cloud.data))

import textwrap
import logging as log
import datetime


def is_IXR_Date(s):
	return s.startswith('O:8:"IXR_Date":7:{')

def IXR_Date(datetime_obj):
	# 2020-12-31 12:00:00
	# O:8:"IXR_Date":7:{s:4:"year";s:4:"2020";s:5:"month";s:2:"12";s:3:"day";s:2:"31";s:4:"hour";s:2:"12";s:6:"minute";s:2:"00";s:6:"second";s:2:"00";s:8:"timezone";s:0:"";}
	
	s = str(datetime_obj)
	
	ixr = 'O:8:"IXR_Date":7:{' + 's:4:"year";s:4:"{year}";s:5:"month";s:2:"{month}";s:3:"day";s:2:"{day}";s:4:"hour";s:2:"{hour}";s:6:"minute";s:2:"{minute}";s:6:"second";s:2:"{second}"'.format(
		year=s[0:4],
		month=s[5:7],
		day=s[8:10],
		hour=s[11:13],
		minute=s[14:16],
		second=s[17:19]
	) + ';s:8:"timezone";s:0:"";}'
	
	return ixr


def sanitize_value(value):
	if type(value) is bool:
		if (value):
			value = 1
		else:
			value = 0
	
	if type(value) is int:
		value = str(value)

	if type(value) is datetime.datetime:
		value = value.strftime("%Y-%m-%d %H:%M:%S")
	
	if value == None:
		value = ""

	return value	


def sanitize_value4log(s):
	if type(s) is datetime.datetime:
		s = s.strftime("%Y-%m-%d %H:%M:%S")
	
	if type(s) is str:
		s.replace('\n', ' ').replace('\r', '')
		s = textwrap.shorten(s, width=30)
	return s


def is_different(a, b):
	log.debug("Comparing {ta} with {tb}".format(ta=type(a), tb=type(b)))
	if type(a) == type(b):
		return a != b
	else:
		return convertValue(a) != convertValue(b)

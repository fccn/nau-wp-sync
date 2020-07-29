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
	if value is None:
		return value
	
	if type(value) is bool:
		if value:
			return 1
		else:
			return 0
	
	if type(value) is int:
		return value
	
	if type(value) is datetime:
		return value
	
	return value


def sanitize_value4log(s):
	if type(s) is str:
		s.replace('\n', ' ').replace('\r', '')
		s = textwrap.shorten(s, width=30)
	return s


def is_different(a, b):
	log.debug("Comparing {ta} with {tb}".format(ta=type(a), tb=type(b)))

    # IXR_Date is str type with a special format
	# it is easier to convert datetime into IXR_Date than IXR_Date in datetime
	# convert datetime into IXR_Date if detected.

	if type(b) is str and type(a) is datetime.datetime:
		if is_IXR_Date(b):
			a=IXR_Date(a)
	
	if type(b) is datetime.datetime and type(a) is str:
		if is_IXR_Date(a):
			b=IXR_Date(b)
	
	if type(a) == type(b):
		return a != b
	
	if type(a) is bool:
		if (a):
			a = 1
		else:
			a = 0
	
	if type(b) is bool:
		if (b):
			b = 1
		else:
			b = 0
	
	if type(a) is int:
		a = str(a)
	
	if type(b) is int:
		b = str(b)
	
	if type(a) is datetime.datetime:
		a = a.strftime("%Y-%m-%d %H:%M:%S")
	
	if type(b) is datetime.datetime:
		b = b.strftime("%Y-%m-%d %H:%M:%S")
	
	if a == None:
		a = ""
	
	if b == None:
		b = ""
	
	return a != b

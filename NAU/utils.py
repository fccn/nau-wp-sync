import textwrap
import logging as log
import datetime

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

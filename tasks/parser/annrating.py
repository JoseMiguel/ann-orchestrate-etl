from bs4 import BeautifulSoup
import time
import numpy as np
import logging
from collections import defaultdict
from  tasks.core.base import SiteTask, OrchestrateTask
import urllib2
from porc import Client

class ANNRatingOrchestrate(OrchestrateTask):

	@property
	def id(self):
		return 3

	def __init__(self):
	
		logging.basicConfig(filename=self.conf['logs']['crawler'],
						format='%(asctime)s - %(levelname)s:%(message)s', 
						level=logging.DEBUG,
						datefmt='%m/%d/%Y %I:%M:%S %p')

	def run(self):
		task = ANNRatingTask()
		self.json = task.run()
		for key, info in self.json.iteritems():
			
			self.key = key
			item = self.get()
			if item.response.status_code == 404:
				self.json = info
			else:				
				item.json['rating'].extend(info['rating'])
				self.json = item.json
			
			self.put()

class ANNRatingTask(SiteTask):

	def __init__(self):
		self.key = ''

	@property	
	def id(self):
		return 3

	def request_url(self):
		return self.site['api_url']
		

	def retrieve(self, leafXML, element):
		attrs = {}
		if element['property'] != None:
			attrs = {element['property'] : element['value']} 

		return leafXML.findAll(element['tag'], attrs=attrs)

	def prepare_url(self,url):
		try:
			xml = urllib2.urlopen(url)
		except Exception as e:
			logging.warning('Failed info in % with key %d, raise: ', self.source, self.key, e.message)
			return None

		return xml
		

	def run(self):
		url = self.request_url()
		xml = self.prepare_url(url)
		return self.crawl(xml, self.elements)

	def crawl(self, xml, elements):
		result = defaultdict(list)
		if xml != None:
			logging.info('Getting anime info from %s with key %s', self.source, self.key)
			soupXML = BeautifulSoup(xml)
			soupTable = self.retrieve(soupXML, self.elements['content'])[0]
		
			for rowSoup in self.retrieve(soupTable, self.elements['row']):
				animeSoup = self.retrieve(rowSoup, self.elements['anime'])
				rankSoup = self.retrieve(rowSoup, self.elements['rank'])
				if animeSoup:
					animeSoup = animeSoup[0]
					element = self.elements['anime_url']
					urlSoup = self.retrieve(animeSoup, element)
					if urlSoup:
						animeUrl = urlSoup[0][element['inplace']]
						animeId = animeUrl[animeUrl.rfind('=')+1:]
						rating, votes = map(lambda r: float(r.text), rankSoup)
						result[animeId] = { 
							'rating': [
										{
											'score': rating, 
											'votes': int(votes), 
											'timestamp': int(time.time()) 
										}
									] 
							}

		return result
	
def main():
#	ann = ANNRatingOrchestrate()
#	ann.run()
	pass

if __name__ == '__main__':
	main()

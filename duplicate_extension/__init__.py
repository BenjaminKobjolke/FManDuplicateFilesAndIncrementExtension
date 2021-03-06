from fman import DirectoryPaneCommand, DirectoryPane, ApplicationCommand, show_alert, FMAN_VERSION, DirectoryPaneListener, load_json, save_json, show_prompt, YES, NO
from fman.fs import copy, move, exists
from fman.url import as_human_readable, basename
from subprocess import Popen
import os.path
import re

class Duplicate(DirectoryPaneCommand):
	def __call__(self):
		paths = self.pane.get_selected_files()

		if len(paths) > 5:
			lengthString = str(len(paths))			
			# confirm if user wants to continue
			choice = show_alert(
					"You selected " + lengthString + " files. Do you want to continue?",
				buttons=YES | NO,
				default_button=NO
			)
			if choice == NO:
				return			

		# iterate paths
		for path in paths:						
			name, ext = os.path.splitext(path)	
			# split string on underscore
			name_split = name.split("_")
			# get last element
			last_element = name_split[-1]
			
			# check if last element is a number
			if re.match(r'\d+', last_element):
				#show_alert(last_element)	
				# all elements except last
				filename = name_split[:-1]
				# join elements
				filename = "_".join(filename)
				digitLength = len(last_element)
				digit = int(last_element)
				digit += 1
				digitString = str(digit)
				name = filename + "_" + digitString.zfill(digitLength)
				#show_alert(name)
				if exists(name + ext):
					show_alert("File already exists " + basename(name + ext))
					continue
			else: 
				name = name + "_copy"

			copypath = name +  ext
			#show_alert(copypath)
			copy(path, copypath)

		self.pane.clear_selection() 
			

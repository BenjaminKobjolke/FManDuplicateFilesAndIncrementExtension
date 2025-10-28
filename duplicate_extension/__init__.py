from fman import DirectoryPaneCommand, DirectoryPane, ApplicationCommand, show_alert, FMAN_VERSION, DirectoryPaneListener, load_json, save_json, show_prompt, YES, NO
from fman.fs import copy, move, exists
from fman.url import as_human_readable, basename, dirname
from subprocess import Popen
import os.path
import re

class Duplicate(DirectoryPaneCommand):
	def _get_filename_parts(self, path):
		"""Extract filename and extension from fman URL path.
		Returns: (filename_without_ext, ext)
		"""
		name, ext = os.path.splitext(path)
		name = basename(name)
		return name, ext

	def _extract_pattern_info(self, path):
		"""Extract base pattern, number, and metadata from a filename.
		Returns: (pattern_type, base_pattern, number, digit_length, ext, v_prefix)
		pattern_type: 'version', 'underscore_number', 'trailing_number', 'leading_number_underscore', 'leading_number_no_underscore', 'pure_number', 'no_number'
		"""
		name, ext = self._get_filename_parts(path)
		name_split = name.split("_")
		last_element = name_split[-1]

		# check if last element is a version pattern (e.g., "v3", "v03")
		if re.match(r'^v\d+$', last_element, re.IGNORECASE):
			filename = "_".join(name_split[:-1])
			version_num = re.search(r'\d+', last_element).group()
			digit_length = len(version_num)
			number = int(version_num)
			v_prefix = last_element[0]
			return ('version', filename, number, digit_length, ext, v_prefix)

		# check if last element is a pure number (e.g., "01", "123")
		elif re.match(r'^\d+$', last_element):
			filename = "_".join(name_split[:-1])
			# If filename is empty, this is a pure number (e.g., "260")
			if not filename:
				digit_length = len(last_element)
				number = int(last_element)
				return ('pure_number', '', number, digit_length, ext, None)
			else:
				digit_length = len(last_element)
				number = int(last_element)
				return ('underscore_number', filename, number, digit_length, ext, None)

		# check if filename ends with digits (without underscore, e.g., "Folie8")
		elif re.search(r'\d+$', name):
			match = re.search(r'(\d+)$', name)
			trailing_number = match.group(1)
			digit_length = len(trailing_number)
			number = int(trailing_number)
			base_pattern = name[:match.start()]
			return ('trailing_number', base_pattern, number, digit_length, ext, None)

		# check if first element (after split) is a pure number (e.g., "01_test")
		elif len(name_split) > 1 and re.match(r'^\d+$', name_split[0]):
			first_element = name_split[0]
			base_pattern = "_".join(name_split[1:])
			# Only match if there's actually something after the number
			if base_pattern:
				digit_length = len(first_element)
				number = int(first_element)
				return ('leading_number_underscore', base_pattern, number, digit_length, ext, None)

		# check if filename starts with digits (without underscore, e.g., "01test")
		elif re.search(r'^\d+', name) and '_' not in name:
			match = re.search(r'^(\d+)', name)
			leading_number = match.group(1)
			base_pattern = name[match.end():]
			# Only match if there's actually something after the number
			if base_pattern:
				digit_length = len(leading_number)
				number = int(leading_number)
				return ('leading_number_no_underscore', base_pattern, number, digit_length, ext, None)

		else:
			return ('no_number', name, 0, 0, ext, None)

	def _find_next_available_filenames(self, base_path, base_pattern, start_number, count, digit_length, ext, pattern_type, v_prefix=None):
		"""Find the next 'count' available filenames starting from start_number.
		Returns a list of available filenames (without extension).
		base_path should be the directory URL from fman (e.g., 'file://E:/working/test/')
		"""
		available_names = []
		current_number = start_number

		while len(available_names) < count:
			# Generate the potential filename based on pattern type
			if pattern_type == 'version':
				candidate = base_pattern + "_" + v_prefix + str(current_number).zfill(digit_length)
			elif pattern_type == 'underscore_number':
				candidate = base_pattern + "_" + str(current_number).zfill(digit_length)
			elif pattern_type == 'trailing_number':
				candidate = base_pattern + str(current_number).zfill(digit_length)
			elif pattern_type == 'leading_number_underscore':
				candidate = str(current_number).zfill(digit_length) + "_" + base_pattern
			elif pattern_type == 'leading_number_no_underscore':
				candidate = str(current_number).zfill(digit_length) + base_pattern
			elif pattern_type == 'pure_number':
				candidate = str(current_number).zfill(digit_length)
			else:
				candidate = base_pattern + "_copy"

			# Construct full path using fman URL style
			if base_path.endswith('/'):
				full_path = base_path + candidate + ext
			else:
				full_path = base_path + '/' + candidate + ext

			if not exists(full_path):
				available_names.append(candidate)

			current_number += 1

			# Safety check to avoid infinite loop
			if current_number > start_number + 10000:
				break

		return available_names

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

		# Pre-process: group files by pattern and find highest numbers
		pattern_groups = {}  # key: (pattern_type, base_pattern, ext, digit_length, v_prefix), value: [paths]

		for path in paths:
			pattern_info = self._extract_pattern_info(path)
			pattern_type, base_pattern, number, digit_length, ext, v_prefix = pattern_info

			# Create a key for grouping
			key = (pattern_type, base_pattern, ext, digit_length, v_prefix if v_prefix else '')

			if key not in pattern_groups:
				pattern_groups[key] = []
			pattern_groups[key].append((path, number))

		# For each group, find the highest number and generate available filenames
		path_to_target = {}  # mapping from original path to target name

		for key, file_list in pattern_groups.items():
			pattern_type, base_pattern, ext, digit_length, v_prefix = key

			if pattern_type == 'no_number':
				# Files without numbers get _01, _02, etc. with leading zero
				# Get directory URL for checking existing files
				base_path = dirname(file_list[0][0])

				# Use underscore_number pattern with 2-digit format starting from 01
				available_names = self._find_next_available_filenames(
					base_path,
					base_pattern,
					1,  # Start from 01
					len(file_list),
					2,  # Always use 2 digits (01, 02, ...)
					ext,
					'underscore_number',
					None
				)

				# Assign available names to paths
				for i, (path, _) in enumerate(file_list):
					if i < len(available_names):
						path_to_target[path] = available_names[i]
			else:
				# Find the highest number in this group
				max_number = max(num for _, num in file_list)

				# Get directory URL for checking existing files
				base_path = dirname(file_list[0][0])

				# Find next available filenames starting from max_number + 1
				available_names = self._find_next_available_filenames(
					base_path,
					base_pattern,
					max_number + 1,
					len(file_list),
					digit_length,
					ext,
					pattern_type,
					v_prefix if v_prefix else None
				)

				# Sort file_list by number to maintain order
				file_list.sort(key=lambda x: x[1])

				# Assign available names to paths
				for i, (path, _) in enumerate(file_list):
					if i < len(available_names):
						path_to_target[path] = available_names[i]

		# iterate paths and copy using pre-computed targets
		for path in paths:
			if path in path_to_target:
				target_name = path_to_target[path]
				_, ext = self._get_filename_parts(path)

				# Construct full path: directory + target filename
				base_path = dirname(path)
				if base_path.endswith('/'):
					copypath = base_path + target_name + ext
				else:
					copypath = base_path + '/' + target_name + ext

				# Double-check that target doesn't exist (shouldn't happen with our logic)
				if exists(copypath):
					show_alert("File already exists " + basename(copypath))
					continue

				copy(path, copypath)

		self.pane.clear_selection() 
			

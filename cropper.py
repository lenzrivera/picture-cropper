import os, math
from PIL import Image

# Rate for calculating minimum pixels
# ~75000px image => 100px => 1/750
MIN_PX_RATE   = 1/750

# Lightness threshold (default 0.95)
# RGB values are scaled by PIL from 0 to 255
min_lightness = 0.95*255.0

# Image scale resize toggle
resize   = True
# Resize factor
# (a.k.a picture_ppi/scanner_dpi)
r_factor = 0.5

def set_args(minl, res, dpi, ppi):
	global min_lightness
	min_lightness = minl * 255.0
	
	global resize
	resize = res
	
	global r_factor
	r_factor = ppi/dpi


def _to_coords(i, width):
	"""Converts an array index into a tuple of (x,y)"""
	return divmod(i, width)[::-1]
	
def _get_L(rgb):
	"""Gets the lightness from an RGB tuple"""
	return 0.5 * (max(rgb) + min(rgb))
	

class Cropper:
	"""Class for cropping scanned images"""
	
	def __init__(self, imgdir, n_regions):
		
		# Open the image and get its data in RGB
		self.image 		= Image.open(imgdir)
		self.image_data = self.image.convert("RGB").getdata()
		
		# Get the total pixels for the next few calculations:
		total_pixels = self.image.width * self.image.height
		
		# Number of regions to scan
		self.regions 	= n_regions
		# Minimum pixels for a cropped region
		self.min_pixels = MIN_PX_RATE * total_pixels
		
		# Starting y-coordinate based on the number of regions
		self.y_start 	 = self.image.height / (self.regions * 2)
		# Last index; len(self.image_data)-1
		self.end_index   = total_pixels - 1
		
		# The accumulated crop bounds
		self.cropped_images = []

	
	def crop(self):
		"""Crops a delimited input image file into its constituent images."""
		
		# Scan through all regions:
		for i in range(0, self.regions):

			# Get starting and ending scan indices
			scan_start = self.image.width * math.floor(self.y_start * (2 * i + 1))
			scan_end   = scan_start + self.image.width-1
		
			# Scan rightward from scan_start for images
			curr_index = scan_start
	
			while curr_index < scan_end:
		
				# Find the index bounds of the current image, if any
				start_i = self._find_color(curr_index, scan_end)

				# If no colored pixels are found, 
				# break the loop and start on the next region
				if start_i == False:
					break

				# Find the edge index of the image
				end_i   = self._find_edge(start_i, scan_end, 1)
				
				# Get the image's rect bounds
				bounds = self._get_bounds(start_i, end_i, scan_start)
		
				# If the image bounds are not too small, crop the image using it
				if bounds is not False:
				
					# Crop and resize the child image from the bounds
					resized_crop = self._crop_and_resize(bounds)
					
					# Append to cropped image list
					self.cropped_images.append(resized_crop)
					
				# Start the next scan from the pixel after the image edge
				curr_index = end_i + 1
	
	def save_and_close(self, cropped_dir):
		
		# Close the input image; the rest of the  
		# processing will be done on the cropped images
		self.image.close()
		
		# Get the image filename
		imgname = os.path.basename(self.image.filename)
		
		# Get the number of detected cropped images
		img_amt = len(self.cropped_images)
		
		# Check if no images were detected/cropped
		if img_amt == 0:
			print("INFO: No croppable images found in " + imgname)
			return
			
		# Save the cropped images
	
		if img_amt == 1:
			self.cropped_images[0].save(cropped_dir + imgname)
			self.cropped_images[0].close()
			
		else:
		
			# Number files in case of multiple images
			
			# This seems to be the best way to universally number files
			filename, extension = os.path.splitext(imgname)	
			
			for i, img in enumerate(self.cropped_images):
				img.save(cropped_dir + filename + "_" + str(i+1) + extension)
				img.close()
	
					
	def _get_bounds(self, start_i, end_i, scan_i):
		"""Returns the rect bounds of a region on the input image"""

		# Distance from start_i to midpoint
		start_dist  = math.floor( (end_i - start_i) * 0.5 )
		# Midpoint index
		midpoint_i	= start_i + start_dist
		# Midpoint x-coordinate
		midpoint_x	= (start_i + start_dist) - scan_i
		# Distance from midpoint to end_i
		end_dist   	= end_i - midpoint_i
	
		# Topmost and bottommost indices from the midpoint
		top_i 	 = self._find_edge(
			midpoint_i, 
			midpoint_x, 
			-self.image.width
		)
		bottom_i = self._find_edge(
			midpoint_i, 
			self.end_index - (self.image.width - midpoint_x - 1), 
			self.image.width
		)
		
		# Get top-left and bottom-right points
		
		top_left 	 = _to_coords( top_i - start_dist, self.image.width )
		# Bottom-right point is offseted by 1, 
		# so we move it down and right by 1
		bottom_right = _to_coords( 
			bottom_i + end_dist + (self.image.width + 1), 
			self.image.width 
		)
	
		# Check for bounds size
		if (
			bottom_right[0] - top_left[0] < self.image.width * 0.25 or
			bottom_right[1] - top_left[1] < self.image.height * 0.25
		):
			return False
		
		return top_left + bottom_right
	
	def _crop_and_resize(self, bounds):
		"""
		Crops a child image from its parent and 
		resizes it (if the option is on) based on scanner dpi
		"""
		
		# Crop the child image from its parent
		cropped_img = self.image.crop(bounds)
		
		# Check if the resize option is false
		if resize is False:
			return cropped_img
		
		# Return the resized image
		return cropped_img.resize(
			( math.floor(cropped_img.width * r_factor), 
			  math.floor(cropped_img.height * r_factor) ),
			Image.BICUBIC
		)
					
				
	def _find_color(self, i_start, i_end):
		"""Scans a scan region for a colored colored pixel
		
		Returns the index of the colored pixel, else False if
		no colored pixels are found within the scan region.
		"""
		
		i = i_start
		while _get_L(self.image_data[i]) >= min_lightness:

			i += 1
			
			if i == i_end:
				return False
	
		return i
		
	def _find_edge(self, i_start, i_end, step):
		"""Scans a scan region for a white pixel
		
		The increment and direction are determined 
		by the step.
		
		Returns the index of the last scanned pixel,
		white or not.
		"""

		i = i_start + step
		while _get_L(self.image_data[i]) < min_lightness:
	
			if i == i_end:
				# No white pixels in the scan range
				return i_end
			
			i += step
			
		return i - step
		

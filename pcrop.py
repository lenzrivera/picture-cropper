import os, sys, argparse
import cropper

def parse_args():
	"""Parses command line arguments:
	
	scandir -> directory to scan
	
	(optional)
	regions -> number of scan regions 				 (default=2)
	minl	-> minimum lightness/lightness threshold (default=0.95)
	resize  -> image dimension downscaling toggle
	dpi		-> scanner dpi
	ppi		-> preferred image ppi
	"""
	
	parser = argparse.ArgumentParser()
	
	parser.add_argument("scandir", type=str, 
		help="Directory to crop input images"
	)
	
	# Scanner Args
	parser.add_argument("--regions", type=int, default=2, 
		help="Number of regions to scan in the input image (default=2)"
	)
	parser.add_argument("--minl", type=float, default=0.95,
		help="Lightness threshold (default=0.95)"
	)
	
	# Resizer Args
	parser.add_argument("--resize", type=bool, default=True,
		help="""Enables the scaling down of images, 
		considering the scan file and image size (default=true)"""
	)
	parser.add_argument("--sdpi", type=int, default=600,
		help="The scanner dpi (default=600)"
	)
	parser.add_argument("--ppi", type=int, default=300,
		help="Preferred picture ppi (default=300)"
	)
	
	return parser.parse_args()

def read_dir(dir):
	"""Reads a directory and yields all images found"""

	# Note: os.fsencode eliminates the use of unicode 
	# conversion as it encodes the string in raw binary
	for file in os.listdir( os.fsencode(dir) ):
		
		# Yield full path of image file
		yield dir + "\\" + os.fsdecode(file)
	
def get_images(path):
	"""Returns a tuple of image file(s) are to be cropped."""
	
	# Check if file/directory exists
	if os.path.isdir(path):
		return read_dir(path)
	elif os.path.isfile(path):
		return (path, )
	else:
		raise FileNotFoundError(path)

def crop_and_save(imgdir, cropped_dir, n_regions):
	"""Crops the image from imgdir and saves it in cropped_dir"""
	
	# Read the image
	image_cropper = cropper.Cropper(imgdir, n_regions)
	
	# Scan and crop the images from the input image
	image_cropper.crop()
	
	# Save the cropped images and finalize the input image
	image_cropper.save_and_close(cropped_dir)

	
def main(dir, n_regions):

	# Directory name for cropped image(s)
	cropped_dir = dir + "_cropped\\"
	
	# Image files to crop
	to_crop = get_images(dir)
	
	# Make a directory for the cropped images
	os.mkdir(cropped_dir)
	
	# Go through all images in dir and crop each
	for imgdir in to_crop:
		crop_and_save(imgdir, cropped_dir, n_regions)

	
if __name__ == "__main__":
	
	# Parse and set arguments
	args = parse_args()
	cropper.set_args(args.minl, args.resize, args.sdpi, args.ppi)

	try:
		main(args.scandir, args.regions)
		
	except FileExistsError as e:
		print("INFO: It seems that this folder has already been cropped:", file=sys.stderr)
		print(e)

	except FileNotFoundError as e:
		print("ERROR: The directory entered does not exist.", file=sys.stderr)
	
	except Exception as e:
		import traceback
		traceback.print_exc()
	
	finally:
		sys.exit()
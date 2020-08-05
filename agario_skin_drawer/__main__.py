from math import cos, radians, sin, sqrt
from PIL import Image
from pynput.keyboard import Key, Listener as KeyboardListener
from pynput.mouse import Button, Controller as MouseController, Listener as MouseListener
from simple_chalk import chalk
from time import sleep
from typing import Dict, List, Optional, Tuple

Location = Tuple[int, int]
Region = Tuple[int, int, int]
Color = Tuple[int, int, int]

color_header = chalk.bold.blue
color_option = chalk.magenta

def get_region() -> Optional[Region]:
	locations: List[Location] = []
	print(color_header("Calibration Region"))
	print("Please set the editor region by clicking on any 3 of the 4 farthest " \
		"sides on the cell editor. One for the top, left, etc... The order, " \
		"neither the sides matter, as long as you click on a side you haven't " \
		"clicked before.")
	print("Press ESC at any time to cancel.")

	def on_click(x, y, button, pressed):
		if pressed and button == Button.left:
			locations.append((x, y))
			if len(locations) >= 3:
				return False
			else:
				print(f'{3 - len(locations)} more click' \
					f'{"s" if 3 - len(locations) != 1 else ""}...')

	with MouseListener(on_click=on_click) as listener:
		def detect(key):
			if key == Key.esc:
				listener.stop()
				return False

		with KeyboardListener(on_press=detect):
			listener.join()

	if len(locations) != 3:
		print("Calibration canceled.")
		return None
	print("Calibration finished.")

	offset_x = min([x for (x, _) in locations])
	offset_y = min([y for (_, y) in locations])
	diamater = max([
		max([x for (x, _) in locations]) - offset_x,
		max([y for (_, y) in locations]) - offset_y
	])
	return (offset_x, offset_y, diamater)

def highlight_region(region: Region):
	(offset_x, offset_y, diamater) = region
	radius = diamater / 2
	terminated = False
	print(color_header("Highlighting Region"))
	print("Press ESC at any time to cancel.")

	def detect(key):
		nonlocal terminated
		if key == Key.esc:
			terminated = True
			return False

	with KeyboardListener(on_press=detect):
		mouse = MouseController()
		for deg in range(0, 360):
			if terminated:
				break
			rad = radians(deg)
			mouse.position = (
				offset_x + radius + sin(rad) * radius,
				offset_y + radius + cos(rad) * radius
			)
			sleep(0.01)
	if terminated:
		print("Highlighting canceled.")
	else:
		print("Highlighting finished.")

def get_color_spots() -> Optional[Dict[Color, Location]]:
	colors = dict()
	hard_coded_colors = [
		((105, 221, 0), "green"),
		((255, 204, 0), "yellow"),
		((255, 126, 0), "orange"),
		((255, 61, 61), "red"),
		((192, 0, 255), "purple"),
		((255, 62, 212), "magenta"),
		((0, 120, 255), "blue"),
		((0, 222, 255), "cyan"),
		((255, 255, 255), "white"),
		((42, 42, 42), "black")
	]
	print(color_header("Calibrate Color Picker"))

	def on_click(x, y, button, pressed):
		if pressed and button == Button.left:
			colors[hard_coded_colors[len(colors)][0]] = (x, y)

			index = len(colors)
			if index >= len(hard_coded_colors):
				print("Now you're all done!")
				return False
			elif index == 3:
				color = hard_coded_colors[index]
				print(f"Yes, for every color now... And then the {color[1]} dot.")
			else:
				color = hard_coded_colors[index]
				print(f"And then the {color[1]} dot.")

	print(f"First, click the {hard_coded_colors[0][1]} dot.")
	with MouseListener(on_click=on_click) as listener:
		def detect(key):
			if key == Key.esc:
				listener.stop()
				return False

		with KeyboardListener(on_press=detect):
			listener.join()
	if len(colors) == len(hard_coded_colors):
		return colors
	else:
		return None

def draw_image(region: Region, color_location: Dict[Color, Location]):
	terminated = False
	colors = color_location.keys()
	print(color_header("Drawing Image"))
	print("Be sure to select the smallest brush for best quality.")

	def detect(key):
		nonlocal terminated
		if key == Key.esc:
			terminated = True
			return False

	def distance(c1, c2):
		(r1, g1, b1) = c1
		(r2, g2, b2) = c2
		return sqrt((r1 - r2) ** 2 + (g1 - g2) ** 2 + (b1 - b2) ** 2)

	with KeyboardListener(on_press=detect):
		image_file = input(color_option("Location of the image file to draw: "))
		print("Don't move your mouse!")
		print("Press ESC at any time to cancel.")

		image = Image.open(image_file)
		image = image.resize((width := int(region[2] / 5), width))

		mouse = MouseController()
		for x in range(0, image.width):
			if terminated:
				break
			for y in range(0, image.height):
				if terminated:
					break

				color = image.getpixel((x, y))
				nearest_color = sorted(colors, key=lambda c: distance(c, color))[0]

				mouse.position = color_location[nearest_color]
				mouse.press(Button.left)
				mouse.release(Button.left)

				mouse.position = (region[0] + x * 5, region[1] + y * 5)
				mouse.press(Button.left)
				mouse.release(Button.left)

def main():
	first = True
	region = None
	colors = None

	def true():
		return True

	def do_help():
		print(color_header("Help"))

		what_to_do_next = None
		if region is None:
			what_to_do_next = f'Run {color_header("Calibrate Region")} to ' \
				"calibrate the location of your skin editor, then run " \
				f'{color_header("Highlight Region")} to confirm your selection is ' \
				"correct."
		elif colors is None:
			what_to_do_next = f'Run {color_header("Calibrate Color Picker")} to ' \
				"calibrate the location of your skin editor's color pallete."
		else:
			what_to_do_next = f'Run {color_header("Draw Image")} to draw any image ' \
				"to the canvas. Once you're done, you can run " \
				f'{color_header("Exit")}, or press Ctrl + C to exit.'

		print("What To Do Next")
		print(what_to_do_next)
		print()
		print("More details will be provided in a later version.")

	def do_calibrate_region():
		nonlocal region
		region = get_region()

	def do_highlight_region():
		assert region is not None
		highlight_region(region)

	def check_highlight_region():
		return not not region

	def do_calibrate_color_picker():
		nonlocal colors
		colors = get_color_spots()

	def do_draw_image():
		assert region is not None
		assert colors is not None
		draw_image(region, colors)

	def check_draw_image():
		return not not region and not not colors

	options = [
		("Exit", exit, true),
		("Help", do_help, true),
		("Calibrate Region", do_calibrate_region, true),
		("Highlight Region", do_highlight_region, check_highlight_region),
		("Calibrate Color Picker", do_calibrate_color_picker, true),
		("Draw Image", do_draw_image, check_draw_image)
	]

	while True:
		filtered_options = [option for option in options if option[2]()]

		if not first:
			print()
		print(color_header("Menu"))
		for index, option in enumerate(filtered_options):
			print(f"{color_option(f'{index}:')} {color_header(option[0])}")

		chosen = int(input(color_option("Pick an option: ")))
		chosen = filtered_options[chosen][1]
		if chosen != exit:
			print()
		chosen()
		first = False

try:
	main()
except KeyboardInterrupt:
	print()

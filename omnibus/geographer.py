
from shapely.geometry import Point

class Geographer():

	def __init__(self):
		pass

	def tile_index(point, res_x, res_y, min_x, min_y, max_x, max_y, grid_index):
		pass
		#if point.x >= min_x and point.x < max_x and point.y <= max_y and point.y > min_y:
		#	return (floor((point.x - min_x) / res_x)
		#	floor((point.y - min_y) / res_y)

	def retrieve_elevation():
		pass


def convert_rd_to_wgs84(x, y):
	coeff_k = ((0, 1, 3235.65389), (2, 0, -32.58297), (0, 2, -0.24750), (2, 1, -0.84978),
		(0, 3, -0.06550), (2, 2, -0.01709), (1, 0, -0.00738), (4, 0, 0.00530),
		(2, 3, -0.00039), (4, 1, 0.00033), (1, 1, -0.00012))

	coeff_l = ((1, 0, 5260.52916), (1, 1, 105.94684), (1, 2, 2.45656), (3, 0, -0.81885), 
		(1, 3, 0.05594), (3, 1, -0.05607), (0, 1, 0.01199), (3, 2, -0.00256), 
		(1, 4, 0.00128), (0, 2, 0.00022), (2, 0, -0.00022), (5, 0, 0.00026))

	dx = lambda x, k : pow((x - 155000) * 1e-5, k)
	dy = lambda y, l : pow((y - 463000) * 1e-5, l)

	phi = 0
	for k in coeff_k:
		phi += dx(x, k[0]) * dy(y, k[1]) * k[2]
	phi /= 3600
	phi += 52.15517440

	lam = 0
	for l in coeff_l:
		lam += dx(x, k[0]) * dy(y, l[1]) * l[2]
	lam /= 3600
	lam += 5.38720621

	return Point(round(phi, 8), round(lam, 8))


def convert_wgs84_to_rd(lon, lat):
	coeff_r = ((0, 1, 190094.945), (1, 1, -11832.228), (2, 1, -114.221), (0, 3, -32.391),
		(1, 0, -0.705), (3, 1, -2.340), (1, 3, -0.608), (0, 2, -0.008), (2, 3, 0.148))

	coeff_s = ((1, 0, 309056.544), (0, 2, 3638.893), (2, 0, 73.077), (1, 2, -157.984), 
		(3, 0, 59.788), (0, 1, 0.433), (2, 2, -6.439), (1, 1, -0.032), (0, 4, 0.092),
		(1, 4, -0.054))

	dphi = lambda lat, r : pow(0.36 * (lat - 52.15517440), r)
	dlam = lambda lon, s : pow(0.36 * (lon - 5.38720621), s)

	x = 0
	for r in coeff_r:
		x += dphi(lat, r[0]) * dlam(lon, r[1]) * r[2]
	x += 155000

	y = 0
	for s in coeff_s:
		y += dphi(lat, s[0]) * dlam(lon, s[1]) * s[2]
	y += 463000

	return Point(round(x, 3), round(y, 3))

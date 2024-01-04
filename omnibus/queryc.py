
from omnibus.config import dataset_config, source, crs_config
import omnibus.passworder as pwd
from omnibus.query import *
from omnibus.geographer import convert_wgs84_to_rd, convert_rd_to_wgs84
from omnibus.database import db

from sqlalchemy import text

class Query:

	def __init__(self, query):
		self.query = query
		self.query_params = []
		self.response = {}

	def validate_variables(self):
		
		# Check for undefined parameters in query
		if unknown := self.unknown_parameter_present():
			self.response["status"] = "INVALID_REQUEST"
			self.response["messages"] = "Invalid parameter found: {}".format(unknown)
			return False

		# Check if all the required parameters are provided with no duplicates
		for i in self.params_required:
			if self.parameter_present(i) and self.parameter_unique(i):
				self.query_params.append(i)
			else:
				self.response["status"] = "INVALID_REQUEST"
				self.response["messages"] = "Query is missing or contains duplicate parameters: {}".format(i)
				return False

		# Check if optional parameters are present in query
		for i in self.params_optional:
			if self.parameter_present(i):
				if self.parameter_unique(i):
					self.query_params.append(i)
				else:
					self.response["status"] = "INVALID_REQUEST"
					self.response["messages"] = "Query is missing or contains duplicate parameters: {}".format(i)
					return False
		
		return True

	def validate_key(self):

		# Search key in database of keys
		rawkey = self.query.get("key")

		try:
			prefix, suffix = rawkey.split(".")
			qkey = "{}.{}".format(prefix, pwd.pwd_hash(suffix))
			saved_key = db.execute(text("SELECT apikey FROM apikey WHERE apikey = :var1"), {"var1": qkey}).first()[0]
			db.remove()
			print(qkey)
			print(saved_key)
			if qkey == saved_key:
				print("yes")
				return True

		except Exception:
			self.response["status"] = "USER_LIMITATION"
			self.response["messages"] = "Query could not complete due to user settings restrictions"
			return False

			

	def validate_values(self):

		for i in self.query_params:
			# Skip "key" values, these are handled by validate_key()
			if not i == "key":
				if i == "via":
					via = self.query.get("via")
					points = via.split("|")
					for j in points:
						xy = j.split(",")
						if len(xy) != 2:
							self.response["status"] = "INVALID_REQUEST"
							self.response["messages"] = "Malformed parameter found: {}".format(j)
							return False
						else: 
							try:
								float(xy[0])
								float(xy[1])
							except ValueError:
								self.response["status"] = "INVALID REQUEST"
								self.response["messages"] = "Malformed parameter found: {}".format(j)
								return False

				if i == "dataset":
					if d := self.query.get("dataset") not in dataset_config:
						self.response["status"] = "INVALID_REQUEST"
						self.response["messages"] = "Unrecognized or unavailable datatset for processing: {}".format(d)
						return False

				if i == "crs":
					if c := self.query.get("crs") not in crs_config:
						self.response["status"] = "INVALID_REQUEST"
						self.response["messages"] = "Unrecognized or unavailable CRS for processing: {}".format(c)
						return False
		return True

	def validate(self):

		if not self.validate_variables():
			return False

		if not self.validate_key():
			return False

		if not self.validate_values():
			return False

		return True

	def unknown_parameter_present(self):
		params_all = self.params_required + self.params_optional
		for p in self.query.keys():
			if not p in params_all:
				return p
		return None

	def parameter_present(self, p):
		return self.query.get(p)

	def parameter_unique(self, p):
		return len(self.query.getlist(p)) == 1



class ElevationPointQuery(Query):

	params_required = ["key", "via"]
	params_optional = ["crs", "dataset"]
	via_max_length = 1

	def __init__(self, query):
		super().__init__(query)

	def process(self):

		if not self.validate():
			return self.response
		
		via = self.query.get("via")
		if len(via.split("|")) > self.via_max_length:
			self.response["status"] = "INVALID_REQUEST"
			self.response["messages"] = "Query path ../point/ accepts only a single coordinate"
			return self.response

		xy = via.split(",")
		x = float(xy[0])
		y = float(xy[1])
		ipoint = Point(x, y)

		name_x = "rdx"
		name_y = "rdy"
		convpoint = None

		crs = self.query.get("crs")
		if self.query.get("crs"):
			if crs in crs_config:
				if crs == "wgs84":
					convpoint = convert_wgs84_to_rd(lon = ipoint.x, lat = ipoint.y)
					name_x = "lon"
					name_y = "lat"

		if convpoint:
			point = convpoint
		else:
			point = ipoint
		
		if self.query.get("dataset"):
			dataset = self.query.get("dataset")
		else:
			dataset = "ahn_dsm_5m" # Default dataset, how to set default?

		# Check sources if coordinate is located with a region
		self.response["results"] = []
		for i in source.keys():
			for j in source[i]:
				if inside_region(point, load_json(source[i][j]["region"])):
					name = find_tile(point, load_json(source[i][j]["tiles"]))
					if name == "":
						self.response["status"] = "TILE_ERROR"
						return self.response
					else:
						res = source[i][j]["datasets"][dataset]["resolution"]
						elevation = open_image(point, dataset_config[dataset] + name, res)
						self.response["results"].append({
							"elevation": float(elevation), 
							name_x: format_number(ipoint.x), 
							name_y: format_number(ipoint.y)})
						self.response["metadata"] = {
							"product": dataset,
							"resolution": res }

		if self.response["results"]:
			self.response["status"] = "OK"
		else:
			self.response["status"] = "ZERO_RESULTS"
		return self.response


class ElevationPointsQuery(Query):

	params_required = ["key", "via"]
	params_optional = ["crs", "dataset"]
	via_max_length = 200

	def __init__(self, query):
		super().__init__(query)

	def process(self):

		if not self.validate():
			return self.response
		else:
		
			via = self.query.get("via")
			points = via.split("|")
			if len(points) > self.via_max_length:
				self.response["status"] = "INVALID_REQUEST"
				self.response["messages"] = "Query path ../points/ is limited to 200 points"
				return self.response

			self.response["results"] = []
			for p in points:
				xy = p.split(",")
				x = float(xy[0])
				y = float(xy[1])
				ipoint = Point(x, y)

				name_x = "rdx"
				name_y = "rdy"
				convpoint = None

				crs = self.query.get("crs")
				if self.query.get("crs"):
					if crs in crs_config:
						if crs == "wgs84":
							convpoint = convert_wgs84_to_rd(lon = ipoint.x, lat = ipoint.y)
							name_x = "lon"
							name_y = "lat"

				if convpoint:
					point = convpoint
				else:
					point = ipoint
				
				if self.query.get("dataset"):
					dataset = self.query.get("dataset")
				else:
					dataset = "ahn_dsm_5m" # Default dataset, how to set default?

				# Check sources if coordinate is located with a region
				for i in source.keys():
					for j in source[i]:
						if inside_region(point, load_json(source[i][j]["region"])):
							name = find_tile(point, load_json(source[i][j]["tiles"]))
							if name == "":
								self.response["status"] = "TILE_ERROR"
								return self.response
							else:
								res = source[i][j]["datasets"][dataset]["resolution"]
								elevation = open_image(point, dataset_config[dataset] + name, res)
								self.response["results"].append({
									"elevation": float(elevation), 
									name_x: format_number(ipoint.x), 
									name_y: format_number(ipoint.y)})

								self.response["metadata"] = {
									"product": dataset,
									"resolution": res }


			if self.response["results"]:
				self.response["status"] = "OK"
			else:
				self.response["status"] = "ZERO_RESULTS"
			return self.response



class SourceQuery(Query):

	params_required = ["key", "via"]
	params_optional = []
	via_max_length = 1

	def __init__(self, query):
		super().__init__(query)

	def process(self):
		if not self.validate():
			return self.response
		else:

			via = self.query.get("via")
			if len(via.split("|")) > self.via_max_length:
				self.response["status"] = "INVALID_REQUEST"
				self.response["messages"] = "Query path ../source/ accepts only a single coordinate"
				return self.response

			xy = via.split(",")
			x = float(xy[0])
			y = float(xy[1])
			point = Point(x, y)

			self.response["results"] = []
			for i in source.keys():
				for j in source[i]:
					polygon = load_json(source[i][j]["region"])
					if inside_region(point, polygon):

						for k in source[i][j]["datasets"]:
							self.response["results"].append({k: source[i][j]["datasets"][k]})

			if self.response["results"]:
				self.response["status"] = "OK"
			else:
				self.response["status"] = "ZERO_RESULTS"
			return self.response



if __name__ == "__main__":
	text = "Hello wOrld"
	q = Query(text)

	q.somefunc()

	eq = ElevationQuery(text)
	eq.somefunc()

	print(eq.required)
	print(q.required)
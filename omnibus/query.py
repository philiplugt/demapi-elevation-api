
import rasterio

from shapely.geometry import Point, Polygon, MultiPolygon
import json
from time import perf_counter
#import rasterio
from math import floor, ceil



def format_number(num):
    if num % 1 == 0:
        return int(num)
    else:
        return num


def load_json(filepath):
    '''
    Get the polygon of the area for which elevation rasters are available
    '''
    with open(filepath) as f:
        return json.load(f)
# For loop isn't necessary, unless checking multiple regions
def inside_region(shape, region):
    for i in region['features']:
        poly = Polygon(i['geometry']['coordinates'][0][0])
        return shape.within(poly)

def find_tile(shape, tiles):
    name = ""
    for i in tiles['features']:
        tile = Polygon(i['geometry']['coordinates'][0][0])
        if shape.within(tile):
            name = str(i['properties']['tile'])
    return name
    #print(count)


def open_image(p, name, res):
    with rasterio.open(name) as dem: 
        raster = dem.read(dem.indexes[0])

        img_x = floor((p.x - dem.bounds.left) / res) # Convert RD x to image x
        car_y = floor((p.y - dem.bounds.bottom) / res) # Convert RD y to image y, accounting for inverted coordinates
        img_y = dem.height - car_y - 1
        
        return raster[img_y, img_x]

"""
if __name__ == "__main__":
    ts = perf_counter()

    rasters = {
        "NL_DSM_5m": (5000, 6500, 5),
        "NL_DTM_5m": (5000, 6500, 5)
    }


    #p = Point(162727, 416055)
    p = add_epsilon(Point(160000, 418750))
    i = load_json("bladindex.geojson")
    name = find_tile(p, i)
    print(name)
    open_image(p, name)
    

    te = perf_counter()
    print("Time: " + str(te - ts))
"""
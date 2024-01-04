
dataset_config = {
	"ahn_dsm_5m": "/web/data/geodata/dem/NLD/DSM_5M/R5_",
    "ahn_dsm_05m": "",
    "ahn_dtm_5m": "/web/data/geodata/dem/NLD/DTM_5M/M5_",
    "ahn_dtm_05m": ""
}

crs_config = ["wgs84", "rd"]

source = {
	"nld": {
		"ahn3": {
			"region": "geofiles/nld/ahn_tile_border.geojson",
			"tiles": "geofiles/nld/ahn_tile_index.geojson",
			"datasets": {
				"ahn_dsm_05m": {
					"name": "Actueel Hoogtebestand Nederland 3 (AHN3)",
					"description": "AHN3 digital surface model with a 50cm resolution",
					"organization": "Rijkswaterstaat",
					"year": "2014-2019",
					"website": "https://www.ahn.nl/",
					"license": "CC-0",
					"datum": "Normaal Amsterdams Peil (NAP)",
					"resolution": 0.5
				},

				"ahn_dsm_5m": {
					"name": "Actueel Hoogtebestand Nederland 3 (AHN3)",
					"description": "AHN3 digital surface model with a 5m resolution",
					"organization": "Rijkswaterstaat",
					"year": "2014-2019",
					"website": "https://www.ahn.nl/",
					"license": "CC-0",
					"datum": "Normaal Amsterdams Peil (NAP)",
					"resolution": 5
				},

				"ahn_dtm_05m": {
					"name": "Actueel Hoogtebestand Nederland 3 (AHN3)",
					"description": "AHN3 digital terrain model with a 50cm resolution",
					"organization": "Rijkswaterstaat",
					"year": "2014-2019",
					"website": "https://www.ahn.nl/",
					"license": "CC-0",
					"datum": "Normaal Amsterdams Peil (NAP)",
					"resolution": 0.5
				},

				"ahn_dtm_5m": {
					"name": "Actueel Hoogtebestand Nederland 3 (AHN3)",
					"description": "AHN3 digital terrain model with a 5m resolution",
					"organization": "Rijkswaterstaat",
					"year": "2014-2019",
					"website": "https://www.ahn.nl/",
					"license": "CC-0",
					"datum": "Normaal Amsterdams Peil (NAP)",
					"resolution": 5
				}
			}
		}
	}
}
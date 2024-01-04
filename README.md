
# Demapi - Elevation API
Demapi is an API web app for querying and retrieving DEM (digital elevation model) data. It is a fully functioning application with user account management and payment processing.

<div align="center">
  <img width="451" alt="Demapi logo" src="https://github.com/pxv8780/demapi-elevation-api/assets/22942635/93f2848b-f544-4b1e-abc6-4e4a21aeef4f">
  <p><sup>The Demapi logo as shown on the live website</sup></p>
</div>

### Versioning

Successfully tested and run with Python 3.11

Demapi was programmed in November 2021 and launched in January 2022.

### How to use

This application is not meant for local use. While you can run it with `flask --app application run --debug` this repository does not contain the necessary the SQL database file, DEM raster files, or ENV files to run properly.

Instead, you can use the live website here: [DEMO](https://demapi.lugtaarde.com)

### Details

Demapi was project to test web development with Python and Flask. Because I tend to work a lot with DEMs on the job, I thought it would be a task well suited for making an API. I also wanted to to learn about monetization, as a result Demapi is integrated with Stripe. The focus of Demapi was on functionality and not design. Indeed, the current CSS design leaves plenty room for improvement.

Most of the challenges I encountered pertained to the DEM data, such as how to store and query the data itself. I decided on storing data as files for simplicity. Normally, such data would be stored in PostGIS database. Likewise, I manually indexed the data by keeping track of the location of each file in the form of vectors shapes. Thus, a query will check if a coordinate is within the bounds of the entire dataset, and check the same thing for each individual file until a match is found, then once a match is found the raster value at the coordinate's location within the file is returned. This works quite well, though there is a bug that occurs if the coordinate is exactly on the edge or corner of a data file. In this case it returns nothing, because the coordinate is technically not inside of the vector shape bounds.
<br>
<br>
<div align="center">
  &nbsp;
  <img width="480" alt="Landing page of the website" src="https://github.com/pxv8780/demapi-elevation-api/assets/22942635/35d0de1d-9862-4f84-b172-787dfabfd20d">
  &nbsp;&nbsp;
  <img width="480" alt="Sample web page after having logged in" src="https://github.com/pxv8780/demapi-elevation-api/assets/22942635/0618fcab-55cf-4dc2-bbf2-11a6d8716b66">
  &nbsp;
  <p><sup>The Demapi landing page and the API key page, which can be seen after having logging in</sup></p>
</div>

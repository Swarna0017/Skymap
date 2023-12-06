#datetime libraries
from datetime import datetime
from geopy import Photon
from tzwhere import tzwhere
from pytz import timezone, UTC

# matplotlib to help display the star map
import matplotlib.pyplot as plt

#skyfield for star data
from skyfield.api import Star, load, wgs84
from skyfield.data import hipparcos
from skyfield.projections import build_stereographic_projection

# for creating a GIF out of every iteration
import imageio
import io

#de421 shows the position of Sun and Earth in space
eph=load('de421.bsp')

with load.open(hipparcos.URL) as f:                                         # hipparcus dataset contains star location data            
    stars=hipparcos.load_dataframe(f)

# user inputs
year=int(input("Year: "))
month=int(input("Month: "))
day=int(input("Day: "))
# timestring=input("Specify a time to start the iteration (24 hour format, hh:mm): ")
# hour=int(timestring[0:2])
# minutes=int(timestring[3:])
# name=input("Please enter your name: ")
loc=input("Location: ")
images = []
start_hour=int(input("Please enter the following data in a 24 hour format\nEnter start hour: "))
end_hour=int(input("Enter end hour: "))
time_step=int(input("Enter timestep (in minutes): "))


duration_in_seconds=int(input("The output will be in the form of a GIF file composed of the collection of every iteration.\nDuration of the GIF (in seconds): "))                                                     # GIF duration

for hour in range(start_hour,end_hour+1):                                                    # Iteration loop
    for minutes in range(0, 60, time_step):
                                                                
        when = f'{year}-{month:02d}-{day:02d} {hour:02d}:{minutes:02d}'
        # latest = '2023-04-16 14:11'
        location=f'{loc}'                                                   # setting up the observer location
        locator = Photon(user_agent='myGeocoder')                           # getting the lat,long using geopy
        location = locator.geocode(location, timeout=None)
        lat,long =location.latitude, location.longitude
        # getting the timezone of the location using pytz libraries
        dt = datetime.strptime(when, '%Y-%m-%d %H:%M')                      # convert date string into datetime object
        # print(dt)
        # print(type(dt))
        # year=int(dt[0:4])
        # year=dt.strftime('%Y')
        # print(year)
        date_time=dt.strftime("%Y-%m-%d, %H:%M:%S")
        # print(date_time)
        timezone_str =tzwhere.tzwhere().tzNameAt(lat,long)                  # defining datetime and converting to UTC based on our timezone
        local =timezone(timezone_str)
        local_dt=local.localize(dt, is_dst=None)                            # get UTC from local timezone and datetime       
        utc_dt=local_dt.astimezone(UTC)
        Sun=eph['Sun']                                                      # find location of earth and sun and set the observer position
        Earth=eph['Earth']
        ts=load.timescale()                                                 # defining observation time from our UTC datetime
        t=ts.from_datetime(utc_dt)
        observer=wgs84.latlon(latitude_degrees=lat,longitude_degrees=long).at(t)    # observer definition using the world geodetic system data
        position=observer.from_altaz(alt_degrees=90,az_degrees=0)
        ra, dec, distance =observer.radec()                                 # calulating star positions
        center_object = Star(ra=ra, dec=dec)                                # (by creating a fake star right above our heads, at 90 degrees lat)
        center=Earth.at(t).observe(center_object)                           # stereographic projection
        projection=build_stereographic_projection(center)
        star_positions = Earth.at(t).observe(Star.from_dataframe(stars))    # observing,projecting by calculating their positions in 2d
        stars['x'],stars['y'] = projection(star_positions)
        
        chart_size=10                                                       # plotting the star chart
        max_star_size=100
        limiting_magnitude=5

        bright_stars = (stars.magnitude <= limiting_magnitude)
        magnitude=stars['magnitude'][bright_stars]

        # plt.clf()
        fig, ax=plt.subplots(figsize=(chart_size, chart_size))          
        border=plt.Circle((0,0), 1.5, color='black', fill=True)             # A dark blue circle of radius=1.5 centered at (0,0)
        ax.add_patch(border)


        marker_size=max_star_size *10**(magnitude/-2.5)                     # calculating the star marker size

        ax.scatter(stars['x'][bright_stars], stars['y'][bright_stars], s=marker_size, color='white', marker='*', linewidths=0, zorder=2)

        # Clipping the horizon to remove everything outside of the dark circle
        horizon= plt.Circle((0,0), radius=1.5, transform=ax.transData)
        for col in ax.collections:
            col.set_clip_path(horizon)

        # ax.set_xlim(-1,1)
        # ax.set_ylim(-1,1)
        ax.set(xlim=(-1,1), ylim=(-1,1))
        plt.axis('off')
        plt.legend([f"Skymap on {date_time}"], loc="upper left")

        ax.text(0.5, -0.93, f'{loc}', color='white', style='oblique', fontsize=11)
                
        # Saving to a BytesIO buffer
        buffer= io.BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)

        # Appending the iterated image to the list
        images.append(imageio.imread(buffer))
        plt.clf()

imageio.mimsave(f'Skymap on {year:02d}.{month:02d}.{day:02d}.gif', images, duration=duration_in_seconds )
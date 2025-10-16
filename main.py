import pandas as pd
import folium

pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)

# set folder pathing
folder = "C:/GardenGroveTransport/"

# load the main files
routes = pd.read_csv(folder + "routes.txt")
stops = pd.read_csv(folder + "stops.txt")
trips = pd.read_csv(folder + "trips.txt")
stop_times = pd.read_csv(folder + "stop_times.txt")

# overview
print("Routes:", routes.shape)
print("Stops:", stops.shape)
print("Trips:", trips.shape)
print("Stop Times:", stop_times.shape)

print(routes.head())

#gather the general area around Garden Grove
lat_min, lat_max = 33.73, 33.82
lon_min, lon_max = -117.97, -117.90

print(stops[['stop_lat', 'stop_lon']].head())


#convert the lon and lat to numbers instead of text
stops['stop_lat'] = pd.to_numeric(stops['stop_lat'], errors='coerce')
stops['stop_lon'] = pd.to_numeric(stops['stop_lon'], errors='coerce')

#remove any stops that don't have any coordinates
stops = stops.dropna(subset=['stop_lat', 'stop_lon'])

#filter stops that are within Garden Grove's area
gg_stops = stops[
    (stops['stop_lat'] >= lat_min) &
    (stops['stop_lat'] <= lat_max) &
    (stops['stop_lon'] >= lon_min) &
    (stops['stop_lon'] <= lon_max)]

#print stops info from Garden Grove
print("\n--- Bus stops within Garden Grove ---")
print("Total stops found: ", len(gg_stops))
print(gg_stops.head())

#create an interactive map of the stops
#choose a starting point(i choose center in this case)
center_lat = (lat_min + lat_max) / 2
center_lon = (lon_min + lon_max) / 2

#create the map based on your starting point
m = folium.Map(location=[center_lat, center_lon], zoom_start=13)

#add the stops as dots on the map
for _, stop in gg_stops.iterrows():
    folium.CircleMarker(
        location=[stop['stop_lat'], stop['stop_lon']],
        radius=4,
        color='blue',
        fill = True,
        fill_opacity = 0.7,
        popup = stop['stop_name']
    ).add_to(m)

#save map as html file
m.save("garden_grove_stops_map.html")

#link the stops to their routes
#merge stop_times with trips to know which trips visits each stop
stop_trips = pd.merge(stop_times, trips[['trip_id', 'route_id']], on='trip_id', how='left')

#merge with the routes to get the names/numbers
stop_routes = pd.merge(stop_trips, routes[['route_id', 'route_short_name', 'route_long_name']], on='route_id', how='left')

#merge with stops for stop names and locations
stop_routes = pd.merge(stop_routes, stops[['stop_id', 'stop_name', 'stop_lat', 'stop_lon']], on='stop_id', how='left')

gg_stop_routes = stop_routes[
    (stop_routes['stop_lat'] >= lat_min) &
    (stop_routes['stop_lat'] <= lat_max) &
    (stop_routes['stop_lon'] >= lon_min) &
    (stop_routes['stop_lon'] <= lon_max)
]

#group by stop to see how many routes serve each one
routes_per_stop = gg_stop_routes.groupby('stop_name')['route_short_name'].nunique().reset_index()
routes_per_stop = routes_per_stop.rename(columns={'route_short_name': 'num_routes'})
print(routes_per_stop.sort_values('num_routes', ascending=False).head(10))

#update the map
for _, stop in gg_stop_routes.iterrows():
    num_routes = routes_per_stop.loc[
        routes_per_stop['stop_name'] == stop['stop_name'], 'num_routes'
    ].values
    color = 'red' if len(num_routes) > 0 and num_routes[0] > 2 else 'blue'

    folium.CircleMarker(
        location=[stop['stop_lat'], stop['stop_lon']],
        radius=4,
        color=color,
        fill = True,
        fill_opacity = 0.7,
        popup = f"{stop['stop_name']} - {num_routes[0] if len(num_routes) > 0 else 0} routes"
    ).add_to(m)

#analyze the average bus frequency per stop
def to_seconds(time_str):
    try:
        h, m, s = map(int, time_str.split(':'))
        return h*3600 + m*60 + s
    except:
        return None

stop_times['arrival_seconds'] = stop_times['arrival_time'].apply(to_seconds)

#merge with stops for location and filtering
stop_visits = pd.merge(stop_times, stops[['stop_id', 'stop_name', 'stop_lat', 'stop_lon']], on='stop_id', how='left')

gg_visits = stop_visits[
    (stop_visits['stop_lat'] >= lat_min) &
    (stop_visits['stop_lat'] <= lat_max) &
    (stop_visits['stop_lon'] >= lon_min) &
    (stop_visits['stop_lon'] <= lon_max)
]

frequency = gg_visits.groupby('stop_name')['trip_id'].count().reset_index()
frequency = frequency.rename(columns={'trip_id': 'num_visits'})

print(frequency.sort_values('num_visits', ascending=False).head(10))

'''The busiest stops are clearly in Harbor Boulevard as it is the primary north-south spine through Garden Grove. High
 stop activity indicates its a major commuter and transfer corridor, likely serving both local riders and intercity connections.
 
 Busiest Stops: 1) Harbor-East Shuttle Area(739 Visits)  2) 1st-Fairview(730 Visits)    3)Harbor-Katella(596 Visits0
 The individual bus stops indicate possible major shopping areas, routes to connecting cities, or tourist attractions(disneyland)
 -->Consider creating an efficient schedule to reduce traffic
 -->Introduce feeder routes or shuttle loops to better connect the area
 
 The repeated 456 visits among the lower stops indicate that there is a regular and evenly timed schedule with many small routes/short trips
 -->Could consider to consolidate some to reduce travel time and improve efficiency 
 
 The analysis of the top bus stop entries revealed that Harbor Blvd as the most heavily trafficked corridor in Garden  Grove, accounting
 for the majority of daily bus stop visits. These serve as the key transfer and high demand points. There also exits opportunities
 to improve coverage in lower traffic zones and increase efficiency overall.
 '''
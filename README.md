# best-weather-in-the-world
Project to find the weather station which reports the best weather
Inspired by numbeo and their climate index, I wanted to find the hidden places in the world with exceptional weather. I did this using data from NOAA's Integrated Surface Database (ISD). I used this database because it keeps dewpoints, which I wanted to take into account. My basic approach to turn raw data into the results I wanted was to give each day for each station a single score, find the average score for the year, then do a weighted average for a station across the 30 years of data.
So what is the best weather? I scored each day by the distance between the heat index and 75 degrees. The heat index was calculated based on the max temp and mean dewpoint for the day. I used heat index because I wanted to punish hot days more than cool days. I also added a function to add to the score for average wind above 10 mph.
I have a branch that also looked at observed weather conditions, but not including them widened the possible stations.
Basic data is here: https://www.ncei.noaa.gov/data/global-summary-of-the-day/archive/

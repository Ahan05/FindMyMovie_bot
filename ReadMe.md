# FindMyMovie_bot
It is a telegram bot that will give you basic information about a movie.

**Bot's nickname: [@find_my_movie_bot](https://t.me/find_my_movie_bot)** 

###Capability
Here is a list of what the bot is capable of:
* With a given movie name, bot asks to choose between several relevant titles 
(with given year of release)
* When bot finds out the movie name it gives your the following information:
genre, release date, rating, description and poster of the movie
* The bot can give you a link where you can watch a trailer or full movie
* At any time you can get list of now-playing movies and get information about them 
(with ```/now``` command)
* Moreover with command ```/sim``` you can get similar to the last searched movie
* Better write movie names in English (cause english database is much bigger), but
if you write title in Russian the bot may find it too.

###Dependencies
Bot uses [TMDB API](https://www.themoviedb.org/documentation/api) to get movie information.
Also the bot parses google-search to find links where you can watch the movie (or trailer)   

###WorkFlow
There is some kind of 2 stage dialogue. At the beginning the bot has state  ```free``` 
and it is ready to receive title. When bot gets the title, it searches for movies 
with relevant titles using TMDB API and asks the user to choose the exact movie. At that 
moment bot's state changes to ```choosing```. After getting the exact title and showing the 
info, bot's state sets to 
```free```.
 
 If bot receives a command while in stage ```choosing```, it start to perform 
the command. If the command is ```/now``` or ```/sim``` bot gets to the ```choosing``` stage 
again and perform the prescribed actions. It commands are  ```/start``` or ```/help``` bots 
state changes to ```free```.


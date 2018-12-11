import requests
import json
import aiohttp
import os
from langid import classify
from requests import get, post
from bs4 import BeautifulSoup
import concurrent.futures
import asyncio
import functools

G_URL = 'https://www.google.ru/search'
DOWNLOAD_FROM = 'https://image.tmdb.org/t/p/w500/'
URL_MOVIE_INFO = 'https://api.themoviedb.org/3/search/movie'
URL_MOVIE_SIMILAR = 'https://api.themoviedb.org/3/movie/'
URL_NOW_PLAYING = 'https://api.themoviedb.org/3/movie/now_playing'
NUMBER_OF_PROP = 4
NUMBER_OF_GENRE = 3

def _make_params_movie(movie_name, up_to_date=False):
    """
    Makes params for GET
    :param movie_name: name of movie
    :param up_to_date: if params needed to get uo_to_date movies
    :return: params for GET
    """
    if up_to_date:
        params = {
            'api_key': os.environ['TMDB_API'],
            'language': 'ru'
        }
    else:
        params = {
            'api_key': os.environ['TMDB_API'],
            'query': movie_name[:-1].split('(')[0],
            'language': classify(movie_name)[0]
        }
    return params


async def google(query):
    """
    Get a link for watching the movie
    :param query: name of movie
    :return: URL
    """
    header = {
        "User-Agent": 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:63.0) Gecko/20100101 Firefox/63.0'
    }
    search_q = "смотреть онлайн " + query
    loop = asyncio._get_running_loop()
    with concurrent.futures.ThreadPoolExecutor() as pool:
        params = (G_URL, {'q': search_q})
        req = await loop.run_in_executor(pool, get, *params)
    text = req.text
    status = req.status_code

    print("google status code: ", status)
    if status != 200:
        print('request failed')
        return ''

    soup = BeautifulSoup(text, "lxml")
    all_links = []
    for i, li in enumerate(soup.findAll('h3', attrs={'class': 'r'})):
        link = li.find('a')
        if link:
            link['href'] = 'http://www.google.com' + link['href']
            all_links.append(link['href'])
    return all_links[1]

async def get_genres(data):
    """
    Get list of genres of film and tagline
    :param data: dict of movies' info
    :return: string of genres and string of tagline
    """
    params = {
        'api_key': os.environ['TMDB_API'],
    }
    URL = 'https://api.themoviedb.org/3/movie/' + str(data['id'])

    async with aiohttp.ClientSession() as session:
        async with session.get(URL, params=params) as resp:
            rsp = await resp.text()

    data = json.loads(rsp)
    return ', '.join([x['name'] for x in data['genres']][:NUMBER_OF_GENRE]), data['tagline']

async def _take_needed_info(data, movie_name, get_movie_list, find_similar, up_to_date):
    """
    Prepossessing of sentences to show to a user.
    :param data: list of found movies with info
    :param movie_name: needed movie name
    :param get_movie_list: whether to return list of movies
    :param find_similar: whether to find similar movies
    :param up_to_date: whether to find up-to-date movies
    :return: Prepossessed sentence to show to user
    """
    if data['results'] == []:
        return None

    movie_list = [result['original_title'] + '(' + result['release_date'].split('-')[0] + ')'
                  for result in data['results']]
    if get_movie_list or find_similar:
        print("Found titles: ", movie_list)
        if up_to_date:
            return list(set(movie_list[:NUMBER_OF_PROP+1]))
        return list(set(movie_list[:NUMBER_OF_PROP]))

    data = data['results'][movie_list.index(movie_name)]
    print("Name of movie is:", data['original_title'])

    link = await google(movie_name)
    data['link'] = ''
    ret_val = await get_genres(data)
    data['genres'], data['tagline'] = ret_val[0], ret_val[1]
    print(data['genres'])

    if link:
        data['link'] = 'Here is a link to watch the movie(or trailer): {}'.format(link)
    if data['poster_path']:
        data['poster_path'] = DOWNLOAD_FROM + data['poster_path']
    if data['overview']:
         data['overview'] = "Description: " + data['overview'] + '\n\n'
    if data['release_date']:
         data['release_date'] = "Release date: " + "/".join(data['release_date'].split('-')[::-1]) +'\n\n'
    else:
        data['release_date'] = "Release date is unknown"
    if data['vote_average']:
        data['vote_average'] = "TMDB rating: " + str(data['vote_average']) + "/10\n\n"
    else:
        data['vote_average'] = ''
    if data['genres']:
        data['genres'] = "Genres: " + data['genres'] + '\n\n'
    if data['tagline']:
        data['tagline'] = 'Tagline: "' +  data['tagline'] + '"\n\n'


    data['general_overview'] = "🍿{}🍿\n\n".format(data['original_title']) + data['tagline'] + data['genres'] +\
                               "🗓 {}".format(data['release_date']) + data['vote_average'] + data['overview'] + \
                               data['link']

    return data

async def get_movie_info(movie_name, get_movie_list = False, find_similar = False, up_to_date = False):
    """
    Send GET request (using TMDB API ) and return list of movies or movie info
    :param movie_name: name of movie to use
    :param get_movie_list: whether to return list of movies
    :param find_similar: whether to find similar movies
    :param up_to_date: whether to find up-to-date movies
    :return: all the information of movies (or one movie)
    """
    # movie_name = movie_name[:-1].split('(')[0]
    params = _make_params_movie(movie_name, up_to_date)
    
    URL = URL_MOVIE_INFO
    if up_to_date:
        URL = URL_NOW_PLAYING
        
    async with aiohttp.ClientSession() as session:
        async with session.get(URL, params=params) as resp:
            rsp = await resp.text()

    data = json.loads(rsp)

    if find_similar:
        URL = 'https://api.themoviedb.org/3/movie/' + str(data['results'][0]['id']) + '/similar'
        async with aiohttp.ClientSession() as session:
            async with session.get(URL, params=params) as resp:
                rsp = await resp.text()
        data = json.loads(rsp)

    needed_info = await _take_needed_info(data, movie_name, get_movie_list, find_similar, up_to_date)
    return needed_info

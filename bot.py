from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
from bot_configs import make_bot
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
import utils.movie_api as movie_api
import utils.sentences as sentences

bot = make_bot()
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

class Form(StatesGroup):
    """
    Here are 2 states:
    1) When bot is free (is waiting for a name)
    2) When bot is trying to get information and give it to user
    """
    free = State()
    choosing = State()

@dp.message_handler(lambda message: message.text not in ["/start", "/help", "/now"], state=None)
async def start_after_shutdown(message: types.Message, state: FSMContext):
    """
    Come here if bot rebooted and I want to continue dialogue.
    """
    await make_choice(message, state)


@dp.message_handler(commands=['start', 'help'], state='*')
async def first_enter(message: types.Message, state: FSMContext):
    """
    The function is called when special commands (start, help) are writen by user
    """
    await Form.free.set()
    print("Message: ", message.text)
    # await state.update_data(last_movie=None)
    if message.text == '/help':
        await bot.send_message(message.chat.id, sentences.HELP_SEN,
                               reply_markup=types.ReplyKeyboardRemove())
    else:
        await bot.send_message(message.chat.id, "Hi there!!! Lets try to find your movie!\n",
                               reply_markup=types.ReplyKeyboardRemove())

@dp.message_handler(commands=['sim'], state='*')
async def similar_movies(message: types.Message, state: FSMContext):
    """
    This is special command. It defines what to to if I want to find similar movies
    """
    await Form.free.set()
    last_movie_name = None
    async with state.proxy() as data:
        if 'last_movie' in data:
            last_movie_name = data['last_movie']

    if last_movie_name is not None:
        print("Is gonna show similar movies")
        await make_choice(message, state, find_similar=True)
    else:
        await bot.send_message(message.chat.id, "There is no movie history yet!",
                               reply_markup=types.ReplyKeyboardRemove())

@dp.message_handler(commands=['now'], state='*')
async def up_to_date_movies(message: types.Message, state: FSMContext):
    """
    This function is called to get list of up-to-date movies
    """
    await Form.free.set()
    print("Is gonna show up-to-date movies")
    await make_choice(message, state, up_to_date=True)


async def start_again(msg: types.Message):
    """
    Comes here if could't find a movie or ended searching
    """
    await bot.send_message(msg.chat.id, "Search for another movie?", reply_markup=types.ReplyKeyboardRemove())


@dp.message_handler(state=Form.free)
async def make_choice(message: types.Message, state: FSMContext, find_similar = False, up_to_date=False):
    """
    This function receives movie name and finds similar, up-tp-date or searching variants and send them to user.
    When in this function, state is set to "Choosing"
    """
    print("Preparing list of movies")

    await Form.choosing.set()
    if find_similar:
        async with state.proxy() as data:
            last_movie_name = data['last_movie']
            movie_list = await movie_api.get_movie_info(last_movie_name, get_movie_list=True,
                                                        find_similar=find_similar)
    elif up_to_date:
        movie_list = await movie_api.get_movie_info(message, get_movie_list=True,
                                                    find_similar=find_similar, up_to_date = up_to_date)
    else:
        movie_list = await movie_api.get_movie_info(message.text, get_movie_list=True)

    if movie_list is None:
        print("There is no movie")
        if find_similar:
            await message.reply("Similar movies for {} not found".format(last_movie_name),
                                reply_markup=types.ReplyKeyboardRemove())
        else:
            await message.reply("Movies not found", reply_markup=types.ReplyKeyboardRemove())
        await Form.free.set()
        await start_again(message)
    else:
        print("Choosing the movie")
        async with state.proxy() as data:
            data['movie_list'] = movie_list

        if len(data['movie_list']) == 1:
            msg = message
            msg.text = data['movie_list'][0]
            await show_movie_info(msg, state)
        else:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True, one_time_keyboard=True)
            for movie_name in movie_list:
                markup.add(movie_name)
            if find_similar:
                await bot.send_message(message.chat.id, "Here are similar movies for {}".format(last_movie_name),
                                       reply_markup=markup)
            elif up_to_date:
                await bot.send_message(message.chat.id, "Here are some now running movies",
                                       reply_markup=markup)
            else:
                await message.reply("Which one is your movie?", reply_markup=markup)

@dp.message_handler(state=Form.choosing)
async def show_movie_info(message: types.Message,  state: FSMContext):
    """
    And this function is called when user chose variant and gives all the information about movie.
    When in this function, state is set to "Choosing"
    """
    async with state.proxy() as data:
        if 'movie_list' in data and message.text not in data['movie_list']:
            await bot.send_message(message.chat.id, "Ok, lets find another one",
                                   reply_markup=types.ReplyKeyboardRemove())
            await make_choice(message, state)

        else:
            await Form.choosing.set()
            movie_info = await movie_api.get_movie_info(message.text)
            print("Is about to show info")
            if movie_info is None:
                await message.reply("Movie not found", reply_markup=types.ReplyKeyboardRemove())
                await Form.free.set()
                await start_again(message)
            else:
                await state.update_data(last_movie=message.text)

                if movie_info['general_overview']:
                    await bot.send_message(message.chat.id, movie_info['general_overview'])
                else:
                    await message.reply("No overview for the movie is available")

                if movie_info['poster_path']:
                    await bot.send_photo(message.chat.id, types.InputFile.from_url(movie_info['poster_path']))
                else:
                    await message.reply( "No poster for the movie is available")

            await Form.free.set()
            await start_again(message)


executor.start_polling(dp)

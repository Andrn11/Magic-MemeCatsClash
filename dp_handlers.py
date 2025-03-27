import logging
from aiogram import dispatcher
from Magicsends import register_magic_handlers
from Start import register_start_handlers
from ValutionTrade import register_valution_trade_handlers
from advanced_logger import register_quest_handlers
from commands import register_commands_handlers, cooldowns
from ledersboard import register_leaderboard_handlers
from shop import register_shop_handlers
from specialcat import register_specialcat_handlers
from MelodyGame import register_melody_handlers
from urprofil import register_urprofil_handlers
from daily_rewards import register_daily_handlers

def register_handlers(dp: dispatcher):
    register_quest_handlers(dp)
    logging.info("Регистрация обработчиков")
    register_daily_handlers(dp)
    register_commands_handlers(dp)
    register_magic_handlers(dp)
    register_shop_handlers(dp, cooldowns)
    register_leaderboard_handlers(dp)
    register_valution_trade_handlers(dp)
    register_start_handlers(dp)
    register_specialcat_handlers(dp)
    register_urprofil_handlers(dp)
    logging.info("Регистрация обработчиков для /profil")
    logging.info("Регистрация обработчиков для /melody")
    register_melody_handlers(dp)


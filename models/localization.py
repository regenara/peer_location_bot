from enum import Enum
from dataclasses import dataclass
from typing import (Dict,
                    Union)


@dataclass
class Languages:
    ru: Union[str, Dict[str, str]] = None
    en: Union[str, Dict[str, str]] = None

    def get(self, lang: Union[Enum, str], **kwargs) -> Union[str, Dict[str, str]]:
        if hasattr(lang, 'value'):
            lang = lang.value
        value = getattr(self, lang)
        if isinstance(value, str):
            value = value.format(**kwargs)
        return value


@dataclass
class Localization:
    hello = Languages()
    languages = Languages()

    back = Languages()
    help_text = Languages()
    wait = Languages()
    in_campus = Languages()
    antiflood = Languages()
    not_found = Languages()
    not_found_username = Languages()
    now = Languages()
    not_logged = Languages()

    coalition = Languages()
    campus = Languages()
    location = Languages()
    ask_adm = Languages()
    piscine = Languages()
    days = Languages()
    hours = Languages()
    minutes = Languages()
    unknown_location = Languages()
    not_on_campus = Languages()
    just_now = Languages()

    locations_title = Languages()
    locations_body = Languages()
    locations_disclaimer = Languages()

    cursus_choose = Languages()
    campus_choose = Languages()
    project_choose = Languages()
    project_title = Languages()
    project_not_found = Languages()

    friends_list = Languages()
    no_friends = Languages()

    observation_on = Languages()
    observation_off = Languages()
    observed_count = Languages()

    add_friend = Languages()
    remove_friend = Languages()
    friends_count = Languages()

    mark = Languages()
    rating = Languages()
    final_mark = Languages()
    not_eval = Languages()
    not_closed = Languages()

    menu = Languages()
    friends = Languages()
    locations = Languages()
    projects = Languages()
    settings = Languages()
    help = Languages()
    about = Languages()
    donate = Languages()
    changed_language = Languages()

    settings_menu = Languages()
    language = Languages()
    avatar = Languages()
    anon = Languages()
    default_campus = Languages()

    last_user = Languages()
    host_not_found = Languages()

    need_auth = Languages()
    auth = Languages()

    donate_text_title = Languages()
    donate_text_tops = Languages()
    donate_link = Languages()

    def load(self, data: dict):
        self.hello.ru = data['hello']['ru']
        self.hello.en = data['hello']['en']
        self.languages.ru = data['languages']['ru']
        self.languages.en = data['languages']['en']

        self.back.ru = data['back']['ru']
        self.back.en = data['back']['en']
        self.help_text.ru = data['help']['ru']
        self.help_text.en = data['help']['en']
        self.wait.ru = data['wait']['ru']
        self.wait.en = data['wait']['en']
        self.in_campus.ru = data['in_campus']['ru']
        self.in_campus.en = data['in_campus']['en']
        self.antiflood.ru = data['antiflood']['ru']
        self.antiflood.en = data['antiflood']['en']
        self.not_found.ru = data['not_found']['ru']
        self.not_found.en = data['not_found']['en']
        self.not_found_username.ru = data['not_found_username']['ru']
        self.not_found_username.en = data['not_found_username']['en']
        self.now.ru = data['now']['ru']
        self.now.en = data['now']['en']
        self.not_logged.ru = data['not_logged']['ru']
        self.not_logged.en = data['not_logged']['en']

        self.coalition.ru = data['user_info']['ru']['coalition']
        self.coalition.en = data['user_info']['en']['coalition']
        self.campus.ru = data['user_info']['ru']['campus']
        self.campus.en = data['user_info']['en']['campus']
        self.location.ru = data['user_info']['ru']['location']
        self.location.en = data['user_info']['en']['location']
        self.ask_adm.ru = data['user_info']['ru']['ask_adm']
        self.ask_adm.en = data['user_info']['en']['ask_adm']
        self.piscine.ru = data['user_info']['ru']['piscine']
        self.piscine.en = data['user_info']['en']['piscine']
        self.days.ru = data['user_info']['ru']['days']
        self.days.en = data['user_info']['en']['days']
        self.hours.ru = data['user_info']['ru']['hours']
        self.hours.en = data['user_info']['en']['hours']
        self.minutes.ru = data['user_info']['ru']['minutes']
        self.minutes.en = data['user_info']['en']['minutes']
        self.unknown_location.ru = data['user_info']['ru']['unknown_location']
        self.unknown_location.en = data['user_info']['en']['unknown_location']
        self.not_on_campus.ru = data['user_info']['ru']['not_on_campus']
        self.not_on_campus.en = data['user_info']['en']['not_on_campus']
        self.just_now.ru = data['user_info']['ru']['just_now']
        self.just_now.en = data['user_info']['en']['just_now']

        self.locations_title.ru = data['free_locations']['ru']['title']
        self.locations_title.en = data['free_locations']['en']['title']
        self.locations_body.ru = data['free_locations']['ru']['body']
        self.locations_body.en = data['free_locations']['en']['body']
        self.locations_disclaimer.ru = data['free_locations']['ru']['disclaimer']
        self.locations_disclaimer.en = data['free_locations']['en']['disclaimer']

        self.cursus_choose.ru = data['projects']['ru']['cursus']
        self.cursus_choose.en = data['projects']['en']['cursus']
        self.project_choose.ru = data['projects']['ru']['choose']
        self.project_choose.en = data['projects']['en']['choose']
        self.campus_choose.ru = data['projects']['ru']['choose_campus']
        self.campus_choose.en = data['projects']['en']['choose_campus']
        self.project_title.ru = data['projects']['ru']['title']
        self.project_title.en = data['projects']['en']['title']
        self.project_not_found.ru = data['projects']['ru']['not_found']
        self.project_not_found.en = data['projects']['en']['not_found']

        self.friends_list.ru = data['friends']['ru']['list']
        self.friends_list.en = data['friends']['en']['list']
        self.no_friends.ru = data['friends']['ru']['no_friends']
        self.no_friends.en = data['friends']['en']['no_friends']

        self.observation_on.ru = data['observations']['ru']['on']
        self.observation_on.en = data['observations']['en']['on']
        self.observation_off.ru = data['observations']['ru']['off']
        self.observation_off.en = data['observations']['en']['off']
        self.observed_count.ru = data['observations']['ru']['count']
        self.observed_count.en = data['observations']['en']['count']

        self.add_friend.ru = data['friends_actions']['ru']['add']
        self.add_friend.en = data['friends_actions']['en']['add']
        self.remove_friend.ru = data['friends_actions']['ru']['remove']
        self.remove_friend.en = data['friends_actions']['en']['remove']
        self.friends_count.ru = data['friends_actions']['ru']['count']
        self.friends_count.en = data['friends_actions']['en']['count']

        self.mark.ru = data['feedbacks']['ru']['mark']
        self.mark.en = data['feedbacks']['en']['mark']
        self.rating.ru = data['feedbacks']['ru']['rating']
        self.rating.en = data['feedbacks']['en']['rating']
        self.final_mark.ru = data['feedbacks']['ru']['final_mark']
        self.final_mark.en = data['feedbacks']['en']['final_mark']
        self.not_eval.ru = data['feedbacks']['ru']['not_eval']
        self.not_eval.en = data['feedbacks']['en']['not_eval']
        self.not_closed.ru = data['feedbacks']['ru']['not_closed']
        self.not_closed.en = data['feedbacks']['en']['not_closed']

        self.menu.ru = data['menu']['ru']
        self.menu.en = data['menu']['en']
        self.friends.ru = data['menu']['ru']['friends']
        self.friends.en = data['menu']['en']['friends']
        self.locations.ru = data['menu']['ru']['locations']
        self.locations.en = data['menu']['en']['locations']
        self.projects.ru = data['menu']['ru']['projects']
        self.projects.en = data['menu']['en']['projects']
        self.settings.ru = data['menu']['ru']['settings']
        self.settings.en = data['menu']['en']['settings']
        self.about.ru = data['menu']['ru']['about']
        self.about.en = data['menu']['en']['about']
        self.donate.ru = data['menu']['ru']['donate']
        self.donate.en = data['menu']['en']['donate']
        self.changed_language.ru = data['changed_language']['ru']
        self.changed_language.en = data['changed_language']['en']

        self.settings_menu.ru = data['settings_menu']['ru']
        self.settings_menu.en = data['settings_menu']['en']
        self.language.ru = data['settings_menu']['ru']['language']
        self.language.en = data['settings_menu']['en']['language']
        self.avatar.ru = data['settings_menu']['ru']['show_avatar']
        self.avatar.en = data['settings_menu']['en']['show_avatar']
        self.anon.ru = data['settings_menu']['ru']['show_telegram']
        self.anon.en = data['settings_menu']['en']['show_telegram']
        self.default_campus.ru = data['settings_menu']['ru']['default_campus']
        self.default_campus.en = data['settings_menu']['en']['default_campus']

        self.last_user.ru = data['host']['ru']['last_user']
        self.last_user.en = data['host']['en']['last_user']
        self.host_not_found.ru = data['host']['ru']['not_found']
        self.host_not_found.en = data['host']['en']['not_found']

        self.need_auth.ru = data['need_auth']['ru']
        self.need_auth.en = data['need_auth']['en']
        self.auth.ru = data['auth']['ru']
        self.auth.en = data['auth']['en']

        self.donate_text_title.ru = data['donate_text']['ru']['title']
        self.donate_text_title.en = data['donate_text']['en']['title']
        self.donate_text_tops.ru = data['donate_text']['ru']['tops']
        self.donate_text_tops.en = data['donate_text']['en']['tops']
        self.donate_link.ru = data['donate_text']['ru']['donate_link']
        self.donate_link.en = data['donate_text']['en']['donate_link']

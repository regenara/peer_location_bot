from datetime import (datetime,
                      timedelta)
from pytz import timezone
from typing import (List,
                    Tuple,
                    Union)

from aiogram.utils.markdown import (hbold,
                                    hcode,
                                    hide_link,
                                    hitalic,
                                    hlink)
from aiogram.utils.parts import paginate

from config import Config
from db_models.campuses import Campus
from db_models.donate import Donate
from db_models.peers import Peer as PeerDB
from db_models.users import User
from models.feedback import Feedback
from models.host import Host
from models.peer import Peer
from utils.intra_api import (UnknownIntraError,
                             NotFoundIntraError)
from utils.savers import Savers


class TextCompile:
    @staticmethod
    async def _get_campus(campus_id: int) -> Campus:
        try:
            campus = await Savers.get_campus(campus_id=campus_id)
        except (UnknownIntraError, NotFoundIntraError):
            campus = Campus(id=campus_id, name=f'Campus id{campus_id}', time_zone='UTC')
        return campus

    @staticmethod
    def _get_utc(iso_format: str) -> float:
        if iso_format:
            return datetime.fromisoformat(iso_format.replace('Z', '+00:00')).timestamp()
        return 0

    @staticmethod
    def _get_str_time(iso_format: str, time_zone: str) -> str:
        if iso_format:
            return datetime.fromisoformat(iso_format.replace('Z', '+00:00')). \
                astimezone(timezone(time_zone)).strftime('%H:%M  %d.%m.%y')

    def _get_log_time(self, begin_at_iso: str, end_at_iso: str, time_zone: str, now: str) -> str:
        begin_at = self._get_str_time(iso_format=begin_at_iso, time_zone=time_zone)
        end_at = self._get_str_time(iso_format=end_at_iso, time_zone=time_zone) or now
        log_time = f'{begin_at} - {end_at}'
        if begin_at[7:] == end_at[7:]:
            log_time = f'{begin_at[:5]} - {end_at[:5]}  {begin_at[7:]}'
        return log_time

    @staticmethod
    def _get_peer_title(status: str, url: str, full_name: str, login: str) -> str:
        return f'{status}{hlink(title=full_name, url=url)} aka {hcode(login)}\n'

    def _get_title_from_message(self, message_text: str) -> str:
        raws = message_text.splitlines()[0].split()
        full_name = ' '.join(raws[1:-2])
        login = raws[-1]
        status = f'{raws[0]} '
        url = f'https://profile.intra.42.fr/users/{login}'
        return self._get_peer_title(status=status, url=url, full_name=full_name, login=login)

    @staticmethod
    def is_wrong_name(name: str) -> str:
        if len(name) > 20:
            return f'{name[:20]}...'
        if len(name) < 2 or any(char in './\\#% \n?!' for char in name):
            return name

    async def peer_data_compile(self, user: User, login: str, is_single: bool) -> Tuple[Union[Peer, None], str]:
        is_wrong = self.is_wrong_name(name=login)
        if is_wrong:
            return None, Config.local.not_found.get(user.language, login=is_wrong.replace("<", "&lt"))
        try:
            peer = await Peer().get_peer(login=login)
        except UnknownIntraError as e:
            return None, f'{hbold(login, ":", sep="")} {e}'
        except NotFoundIntraError:
            return None, Config.local.not_found.get(user.language, login=login.replace("<", "&lt"))
        courses = '\n'.join(
            [f'{hbold(c["cursus"]["name"], ":", sep="")} {round(c["level"], 2)}' for c in peer.cursus_data])
        coalition = ''
        if peer.coalition:
            coalition = f'{hbold(Config.local.coalition.get(user.language), ":", sep="")} {peer.coalition}\n'
        pool = ''
        if peer.pool_month and peer.pool_year:
            months = {
                'january': '01', 'february': '02', 'march': '03',
                'april': '04', 'may': '05', 'june': '06',
                'july': '07', 'august': '08', 'september': '09',
                'october': '10', 'november': '11', 'december': '12'
            }
            pool = f'{hbold(Config.local.piscine.get(user.language), ":", sep="")} ' \
                   f'{months[peer.pool_month]}.{peer.pool_year}\n'
        peer_location = ''
        if peer.is_staff:
            peer_location = Config.local.ask_adm.get(user.language)
        elif peer.location and not peer.is_staff:
            peer_location = hcode(peer.location)
        elif not peer.location:
            peer_location = self._last_seen_time_compile(user=user, last_seen_time=peer.last_seen_time,
                                                         last_location=peer.last_location)
        full_name = hbold(peer.full_name)
        if is_single:
            full_name = hlink(title=peer.full_name, url=peer.link)
        username = ''
        if peer.username:
            username = f'{hbold("Telegram:")} @{peer.username}\n'
        title = f'{peer.status}{full_name} aka {hcode(peer.login)}\n'
        campus = f'{hbold(Config.local.campus.get(user.language), ":", sep="")} {peer.campus}\n'
        location = f'{hbold(Config.local.location.get(user.language), ":", sep="")} {peer_location}'
        text = f'{title}' \
               f'{username}' \
               f'{pool}' \
               f'{coalition}' \
               f'{courses}\n' \
               f'{campus}' \
               f'{location}'
        if user.show_avatar and is_single:
            text = hide_link(url=peer.avatar) + text
        return peer, text

    @staticmethod
    def _last_seen_time_compile(user: User, last_seen_time: str, last_location: str) -> str:
        if not last_seen_time:
            return Config.local.unknown_location.get(user.language)
        seconds = datetime.now(timezone('UTC')).timestamp() - \
            datetime.fromisoformat(last_seen_time.replace('Z', '+00:00')).timestamp()
        seconds_in_day = int(timedelta(days=1).total_seconds())
        seconds_in_hour = int(timedelta(hours=1).total_seconds())
        seconds_in_minute = 60
        days = int(seconds // seconds_in_day)
        hours = int((seconds - (days * seconds_in_day)) // seconds_in_hour)
        minutes = int((seconds - (days * seconds_in_day) - (hours * seconds_in_hour)) // seconds_in_minute)
        days_gone = hours_gone = minutes_gone = ''
        if days:
            days_gone = f'{days}{Config.local.days.get(user.language)} '
        if hours:
            hours_gone = f'{hours}{Config.local.hours.get(user.language)} '
        if minutes:
            minutes_gone = f'{minutes}{Config.local.minutes.get(user.language)} '
        if not any((days, hours, minutes)):
            return Config.local.just_now.get(user.language, last_location=last_location)
        return Config.local.not_on_campus.get(user.language, days_gone=days_gone, hours_gone=hours_gone,
                                              minutes_gone=minutes_gone, last_location=last_location)

    async def peer_locations_compile(self, user: User, login: str, page: int = 0,
                                     message_text: str = None) -> Tuple[str, int]:
        is_wrong = self.is_wrong_name(name=login)
        if is_wrong:
            return Config.local.not_found.get(user.language, login=is_wrong.replace("<", "&lt")), 0
        try:
            locations = await Host().get_peer_locations(login=login)
            if not page:
                peer = await Peer().get_peer(login=login, extended=False)
                title = self._get_peer_title(status=peer.status, url=peer.link,
                                             full_name=peer.full_name, login=peer.login)
            else:
                title = self._get_title_from_message(message_text=message_text)
        except UnknownIntraError as e:
            return f'{hbold(login, ":", sep="")} {e}', 0
        except NotFoundIntraError:
            return Config.local.not_found.get(user.language, login=login.replace("<", "&lt")), 0
        if not locations:
            return Config.local.not_logged.get(user.language, title=title), 0
        count = len(locations[page * 10:])
        locations = paginate(data=locations, page=page, limit=10)
        texts = []
        for location in locations:
            campus = await self._get_campus(campus_id=location.campus_id)
            log_time = self._get_log_time(begin_at_iso=location.begin_at, end_at_iso=location.end_at,
                                          time_zone=campus.time_zone, now=Config.local.now.get(user.language))
            text = f'{hbold(campus.name)} {hcode(location.host)}\n{log_time}'
            texts.append(text)
        return title + '\n'.join(texts), count

    async def host_data_compile(self, user: User, host: str, page: int = 0) -> Tuple[str, Union[Peer, None]]:
        is_wrong = self.is_wrong_name(name=host)
        if is_wrong:
            return Config.local.host_not_found.get(user.language, host=is_wrong.replace("<", "&lt")), None
        try:
            location_records = await Host().get_location_history(host=host)
        except UnknownIntraError as e:
            return f'{hbold(host, ":", sep="")} {e}', None
        except NotFoundIntraError:
            return Config.local.host_not_found.get(user.language, host=host.replace("<", "&lt")), None
        if page < 3:
            location = location_records[page]
            peer, peer_text = await self.peer_data_compile(user=user, login=location.login, is_single=True)
            last_peer = ''
            if not peer:
                peer_text = hcode(location.login)
            else:
                if location.end_at and not page:
                    last_peer = Config.local.last_user.get(user.language)
                else:
                    lines = peer_text.splitlines()
                    if page:
                        peer_text = '\n'.join(lines)
                    else:
                        peer_text = '\n'.join(lines[:-2]).replace('🟢 ', '')
            campus = await self._get_campus(campus_id=location.campus_id)
            log_time = self._get_log_time(begin_at_iso=location.begin_at, end_at_iso=location.end_at,
                                          time_zone=campus.time_zone, now=Config.local.now.get(user.language))
            text = f'🖥 {hbold(campus.name)} {hcode(host)}\n{last_peer}' \
                   f'🕰 {log_time}\n' \
                   f'{peer_text}'
            return text, Peer(id=location.peer_id, login=location.login)
        texts = []
        for location in location_records[3:]:
            campus = await self._get_campus(campus_id=location.campus_id)
            log_time = self._get_log_time(begin_at_iso=location.begin_at, end_at_iso=location.end_at,
                                          time_zone=campus.time_zone, now=Config.local.now.get(user.language))
            text = f'🖥 {hbold(campus.name)} {hcode(host)}\n' \
                   f'🕰 {log_time}\n' \
                   f'👤 {hcode(location.login)}'
            texts.append(text)
        return f'\n\n'.join(texts), None

    async def peer_feedbacks_compile(self, user: User, login: str, page: int = 0,
                                     message_text: str = None) -> Tuple[str, int]:
        is_wrong = self.is_wrong_name(name=login)
        if is_wrong:
            return Config.local.not_found.get(user.language, login=is_wrong.replace("<", "&lt")), 0
        user.show_avatar = False
        try:
            feedbacks = await Feedback().get_peer_feedbacks(login=login)
            if not page:
                peer = await Peer().get_peer(login=login, extended=False)
                title = self._get_peer_title(status=peer.status, url=peer.link,
                                             full_name=peer.full_name, login=peer.login)
            else:
                title = self._get_title_from_message(message_text=message_text)
        except UnknownIntraError as e:
            return f'{hbold(login, ":", sep="")} {e}', 0
        except NotFoundIntraError:
            return Config.local.not_found.get(user.language, login=login.replace("<", "&lt")), 0
        if not feedbacks:
            return Config.local.not_eval.get(user.language, title=title), 0
        count = len(feedbacks[page * 5:])
        feedbacks = paginate(data=feedbacks, page=page, limit=5)
        texts = []
        for feedback in feedbacks:
            final_mark = feedback.final_mark
            if final_mark is None:
                final_mark = Config.local.not_closed.get(user.language)
            text = f'{hbold(feedback.team)} [{feedback.project}]\n' \
                   f'{hbold(login, ":", sep="")} {hitalic(feedback.corrector_comment)}\n' \
                   f'{hbold(Config.local.mark.get(user.language), ":", sep="")} {feedback.mark}\n' \
                   f'{feedback.peer}: {hitalic(feedback.peer_comment)}\n' \
                   f'{hbold(Config.local.rating.get(user.language), ":", sep="")} {feedback.rating}/5\n' \
                   f'{hbold(Config.local.final_mark.get(user.language), ":", sep="")} {final_mark}'
            texts.append(text)
        return title + f'\n{"—" * 20}\n'.join(texts), count

    async def free_locations_compile(self, user: User, campus_id: int, page: int = 0) -> Tuple[str, int, int]:
        campus = await self._get_campus(campus_id=campus_id)
        try:
            scan, active, inactive = await Config.intra.get_campus_locations(campus_id=campus_id,
                                                                             time_zone=campus.time_zone)
        except (UnknownIntraError, NotFoundIntraError) as e:
            return f'{hbold(campus.name, ":", sep="")} {e}', 0, 0
        locations = {}
        for location in inactive:
            if location['host'] not in locations:
                locations.update({location['host']: location})
        for location in active:
            locations.pop(location['host'], '')
        locations = list(locations.items())[:400]
        locations.sort()
        active = len(active)
        now = self._get_str_time(datetime.fromtimestamp(scan).isoformat(), campus.time_zone)
        count = len(locations[page * 40:])
        while not count and page:
            page -= 1
            count = len(locations[page * 40:])
        locations = paginate(data=locations, page=page, limit=40)
        texts = []
        for data in locations:
            location = Host.from_dict(data=data[1])
            end_at = self._get_str_time(iso_format=location.end_at, time_zone=campus.time_zone)
            text = f'{hcode(location.host)}  |  {hcode(location.login)}  |  {end_at}'
            texts.append(text)
        body = Config.local.locations_disclaimer.get(user.language)
        if texts:
            body = Config.local.locations_body.get(user.language)
        title = Config.local.locations_title.get(user.language, campus_name=campus.name, now=now, active=active,
                                                 body=body)
        return title + '\n'.join(texts), count, page

    async def project_peers_compile(self, user: User, project_id: int, campus_id: int) -> str:
        campus = await self._get_campus(campus_id=campus_id)
        try:
            weeks, project_data = await Config.intra.get_project_peers(project_id=project_id, campus_id=campus_id,
                                                                       time_zone=campus.time_zone)
        except (UnknownIntraError, NotFoundIntraError) as e:
            return f'{hbold("Project id", project_id, ":", sep="")} {e}'
        if not project_data:
            project = await Savers.get_project(project_id=project_id)
            project_name = project.name
            return Config.local.project_not_found.get(user.language, campus_name=campus.name, weeks=weeks,
                                                      project_name=project_name.replace("<", "&lt"))
        project_data.sort(key=lambda key: self._get_utc(iso_format=key['marked_at']), reverse=True)
        project_name = project_data[0]['project']['name']
        title = Config.local.project_title.get(user.language, campus_name=campus.name,
                                               project_name=project_name, weeks=weeks)
        texts = []
        for project in project_data[:40]:
            login = project["user"]["login"]
            url = f'https://profile.intra.42.fr/users/{login}'
            marked_at = self._get_str_time(iso_format=project["marked_at"], time_zone=campus.time_zone)
            text = f'{hlink(title=login, url=url)}  |  {project["final_mark"]}  |  {marked_at}'
            texts.append(text)
        return title + '\n'.join(texts)

    @staticmethod
    async def donate_text_compile(user: User) -> str:
        this_month_donates = await Donate.get_last_month_donate()
        tops = await Donate.get_top_donaters()
        sums = []
        nicknames = []
        [[sums.append(donate.sum), nicknames.append(f'{hbold(donate.nickname, ":", sep="")} {hcode(donate.sum)}')]
         for donate in this_month_donates]
        top_nicknames = '\n'.join([f'{hbold(nickname, ":", sep="")} {hcode(sum_)}' for nickname, sum_ in tops])
        text = Config.local.donate_text_title.get(user.language, sum=round(sum(sums), 2),
                                                  nicknames='\n'.join(nicknames))
        if top_nicknames:
            text = text + '\n\n' + Config.local.donate_text_tops.get(user.language, tops=top_nicknames)
        return text

    @staticmethod
    def friends_list_normalization(user: User, message_text: str, friends: List[PeerDB]) -> str:
        friends_data = message_text.split('\n\n')
        friend_logins = [friend.login for friend in friends]
        friends_list = [s for s in friends_data[1:] if any(x in s for x in friend_logins)]
        new_friends_list = []
        for data in friends_list:
            strings = []
            lines = data.splitlines()
            if len(lines) > 1:
                for i, string in enumerate(lines):
                    if not i:
                        strings.append(f'{hbold(string[:string.index("aka")])}'
                                       f'aka {hcode(string[string.index("aka") + 4:])}')
                    else:
                        strings.append(f'{hbold(string[:string.index(":") + 1])}{string[string.index(":") + 1:]}')
            else:
                string = lines[0]
                strings.append(f'{hbold(string[:string.index(":") + 1])}{string[string.index(":") + 1:]}')
            new_friends_list.append('\n'.join(strings))
        if new_friends_list:
            new_friends_list.insert(0, hbold(friends_data[0]))
            return '\n\n'.join(new_friends_list)
        return Config.local.no_friends.get(user.language)


text_compile = TextCompile()

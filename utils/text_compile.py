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
from models.event import Event
from models.feedback import Feedback
from models.host import Host
from models.peer import Peer
from models.project import Project
from utils.cache import Cache
from utils.intra_api import (UnknownIntraError,
                             TimeoutIntraError,
                             NotFoundIntraError)
from utils.savers import Savers


class TextCompile:
    @staticmethod
    async def _get_campus(campus_id: int) -> Campus:
        try:
            campus = await Savers.get_campus(campus_id=campus_id)
        except (UnknownIntraError, NotFoundIntraError, TimeoutIntraError):
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
    def _get_seconds(end_at: str, begin_at: str) -> float:
        end = datetime.fromisoformat(end_at.replace('Z', '+00:00')).timestamp() if \
            end_at else datetime.now(timezone('UTC')).timestamp()
        begin = datetime.fromisoformat(begin_at.replace('Z', '+00:00')).timestamp()
        return end - begin

    @staticmethod
    def _get_time_gone(user: User, seconds: float) -> str:
        seconds_in_year = timedelta(days=365).total_seconds()
        seconds_in_day = timedelta(days=1).total_seconds()
        seconds_in_hour = timedelta(hours=1).total_seconds()
        seconds_in_minute = 60
        years = int(seconds // seconds_in_year)
        days = int((seconds - (years * seconds_in_year)) // seconds_in_day)
        hours = int((seconds - (years * seconds_in_year) - (days * seconds_in_day)) // seconds_in_hour)
        minutes = int((seconds - (years * seconds_in_year) - (days * seconds_in_day) - (hours * seconds_in_hour)) //
                      seconds_in_minute)
        years_gone = f'{years}{Config.local.years.get(user.language)} ' if years else ''
        days_gone = f'{days}{Config.local.days.get(user.language)} ' if days else ''
        hours_gone = f'{hours}{Config.local.hours.get(user.language)} ' if hours else ''
        minutes_gone = f'{minutes}{Config.local.minutes.get(user.language)} ' if minutes else ''
        return ''.join((years_gone, days_gone, hours_gone, minutes_gone))

    def _last_seen_time_compile(self, user: User, last_seen_time: str, last_location: str) -> str:
        if not last_seen_time:
            return Config.local.unknown_location.get(user.language)
        seconds = self._get_seconds(end_at='', begin_at=last_seen_time)
        time_gone = self._get_time_gone(user=user, seconds=seconds)
        if not time_gone:
            return Config.local.just_now.get(user.language, last_location=last_location)
        return Config.local.not_on_campus.get(user.language, time_gone=time_gone, last_location=last_location)

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

    async def _get_peer(self, user: User, login: str) -> Union[Peer, str]:
        is_wrong = self._is_wrong_name(name=login)
        if is_wrong:
            return Config.local.not_found.get(user.language, login=is_wrong.replace("<", "&lt"))
        try:
            return await Peer().get_peer(login=login)
        except (UnknownIntraError, TimeoutIntraError) as e:
            return f'{hbold(login, ":", sep="")} {e}'
        except NotFoundIntraError:
            return Config.local.not_found.get(user.language, login=login.replace("<", "&lt"))

    @staticmethod
    def _is_wrong_name(name: str) -> str:
        if len(name) > 20:
            return f'{name[:20]}...'
        if len(name) < 2 or any(char in './\\#% \n?!' for char in name):
            return name

    @staticmethod
    def _event_cut(event_text: str) -> str:
        if len(event_text) > 4096:
            return event_text[:4000] + '&lt...></i>'
        return event_text

    async def peer_data_compile(self, user: User, login: str, is_single: bool) -> Tuple[Union[Peer, None], str]:
        peer = await self._get_peer(user=user, login=login)
        if isinstance(peer, str):
            return None, peer
        courses = '\n'.join([f'{hbold(cursus.name, ":", sep="")} {cursus.level}' for cursus in peer.cursus_data])
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
        dignity = f'{hitalic(peer.dignity.replace("%login", peer.login))}\n' if peer.dignity else ''
        campus = f'{hbold(Config.local.campus.get(user.language), ":", sep="")} {peer.campus}\n'
        location = f'{hbold(Config.local.location.get(user.language), ":", sep="")} {peer_location}'
        text = f'{title}' \
               f'{dignity}' \
               f'{username}' \
               f'{pool}' \
               f'{coalition}' \
               f'{courses}\n' \
               f'{campus}' \
               f'{location}'
        text = hide_link(url=peer.avatar) + text
        return peer, text

    async def peer_locations_compile(self, user: User, login: str, page: int = 0,
                                     message_text: str = None) -> Tuple[str, int, bool]:
        is_wrong = self._is_wrong_name(name=login)
        if is_wrong:
            return Config.local.not_found.get(user.language, login=is_wrong.replace("<", "&lt")), 0, False
        try:
            locations = await Host().get_peer_locations(login=login)
            if not page:
                peer = await Peer().get_peer(login=login, extended=False)
                title = self._get_peer_title(status=peer.status, url=peer.link,
                                             full_name=peer.full_name, login=peer.login)
            else:
                title = self._get_title_from_message(message_text=message_text)
        except (UnknownIntraError, TimeoutIntraError) as e:
            return f'{hbold(login, ":", sep="")} {e}', 0, False
        except NotFoundIntraError:
            return Config.local.not_found.get(user.language, login=login.replace("<", "&lt")), 0, False
        if not locations:
            return Config.local.not_logged.get(user.language, title=title), 0, True
        count = len(locations[page * 10:])
        locations = paginate(data=locations, page=page, limit=10)
        texts = []
        for location in locations:
            campus = await self._get_campus(campus_id=location.campus_id)
            log_time = self._get_log_time(begin_at_iso=location.begin_at, end_at_iso=location.end_at,
                                          time_zone=campus.time_zone, now=Config.local.now.get(user.language))
            text = f'{hbold(campus.name)} {hcode(location.host)}\n{log_time}'
            texts.append(text)
        return title + '\n'.join(texts), count, True

    async def host_data_compile(self, user: User, host: str, page: int = 0) -> Tuple[str, Union[Peer, None]]:
        is_wrong = self._is_wrong_name(name=host)
        if is_wrong:
            return Config.local.host_not_found.get(user.language, host=is_wrong.replace("<", "&lt")), None
        try:
            location_records = await Host().get_location_history(host=host)
        except (UnknownIntraError, TimeoutIntraError) as e:
            return f'{hbold(host, ":", sep="")} {e}', None
        except NotFoundIntraError:
            return Config.local.host_not_found.get(user.language, host=host.replace("<", "&lt")), None
        if not location_records:
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
                                     message_text: str = None) -> Tuple[str, int, bool]:
        is_wrong = self._is_wrong_name(name=login)
        if is_wrong:
            return Config.local.not_found.get(user.language, login=is_wrong.replace("<", "&lt")), 0, False
        user.show_avatar = False
        try:
            feedbacks = await Feedback().get_peer_feedbacks(login=login)
            if not page:
                peer = await Peer().get_peer(login=login, extended=False)
                title = self._get_peer_title(status=peer.status, url=peer.link,
                                             full_name=peer.full_name, login=peer.login)
            else:
                title = self._get_title_from_message(message_text=message_text)
        except (UnknownIntraError, TimeoutIntraError) as e:
            return f'{hbold(login, ":", sep="")} {e}', 0, False
        except NotFoundIntraError:
            return Config.local.not_found.get(user.language, login=login.replace("<", "&lt")), 0, False
        if not feedbacks:
            return Config.local.not_eval.get(user.language, title=title), 0, True
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
        return title + f'\n{"—" * 20}\n'.join(texts), count, True

    async def free_locations_compile(self, user: User, campus_id: int, page: int = 0) -> Tuple[str, int, int]:
        campus = await self._get_campus(campus_id=campus_id)
        try:
            scan, active, inactive = await Config.intra.get_campus_locations(campus_id=campus_id,
                                                                             time_zone=campus.time_zone)
        except (UnknownIntraError, NotFoundIntraError, TimeoutIntraError) as e:
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
        except (UnknownIntraError, NotFoundIntraError, TimeoutIntraError) as e:
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

    async def peer_projects_compile(self, user: User, login: str) -> Tuple[str, bool]:
        peer = await self._get_peer(user=user, login=login)
        if isinstance(peer, str):
            return peer, False
        title = self._get_peer_title(status=peer.status, url=peer.link, full_name=peer.full_name, login=peer.login)
        if not peer.projects_users:
            return Config.local.not_projects.get(user.language, title=title), True
        projects = Project().from_list(projects_data=peer.projects_users, cursus_data=peer.cursus_data)
        texts = []
        for cursus in projects:
            projects_data = []
            for parent in projects[cursus]:
                children = []
                for child in parent.children:
                    children.append(
                        f'\n  |— {child.status} {child.name} '
                        f'{f" [{child.final_mark}]" if child.final_mark is not None else ""}'
                    )
                projects_data.append(
                    f'{parent.status} {parent.name} '
                    f'{f" [{parent.final_mark}]" if parent.final_mark is not None else ""}{"".join(children)}'
                )
            text = '\n'.join(projects_data)
            texts.append(f'{hbold(cursus)}\n{text}')
        return title + '\n\n'.join(texts), True

    async def time_peers_compile(self, user: User, login: str) -> Tuple[str, bool]:
        is_wrong = self._is_wrong_name(name=login)
        if is_wrong:
            return Config.local.not_found.get(user.language, login=is_wrong.replace("<", "&lt")), False
        try:
            data = await Host().get_peer_locations(login=login, all_locations=True)
            peer = await Peer().get_peer(login=login, extended=False)
            title = self._get_peer_title(status=peer.status, url=peer.link,
                                         full_name=peer.full_name, login=peer.login)
        except (UnknownIntraError, TimeoutIntraError) as e:
            return f'{hbold(login, ":", sep="")} {e}', False
        except NotFoundIntraError:
            return Config.local.not_found.get(user.language, login=login.replace("<", "&lt")), False
        if not data:
            return Config.local.not_logged.get(user.language, title=title), True
        total_seconds = 0
        locations = {}
        maximum = {'seconds': 0}
        for location in data:
            seconds = self._get_seconds(end_at=location.end_at, begin_at=location.begin_at)
            if maximum['seconds'] < seconds:
                maximum.update({
                    'host': location.host, 'campus_id': location.campus_id, 'seconds': seconds,
                    'end_at': location.end_at, 'begin_at': location.begin_at
                })
            locations.setdefault(location.host, {'seconds': 0, 'campus_id': location.campus_id})
            locations[location.host]['seconds'] += seconds
            total_seconds += seconds
        time_gone = self._get_time_gone(user=user, seconds=total_seconds)
        total_time = Config.local.total_time.get(user.language, total=time_gone)
        max_time_campus = await self._get_campus(campus_id=maximum['campus_id'])
        max_time_log = self._get_log_time(begin_at_iso=maximum['begin_at'], end_at_iso=maximum['end_at'],
                                          time_zone=max_time_campus.time_zone, now=Config.local.now.get(user.language))
        max_time_total = self._get_time_gone(user=user, seconds=maximum['seconds'])
        max_time = Config.local.max_time.get(user.language, campus=hbold(max_time_campus.name),
                                             host=hcode(maximum['host']), log_time=max_time_log, total=max_time_total)
        locations = sorted(locations.items(), key=lambda tup: (tup[1]['seconds']), reverse=True)[:10]
        texts = []
        for location in locations:
            campus = await self._get_campus(campus_id=location[1]['campus_id'])
            location_total = self._get_time_gone(user=user, seconds=location[1]['seconds'])
            text = f'🖥 {hbold(campus.name)} {hcode(location[0])}\n' \
                   f'⏱ {location_total}'
            texts.append(text)
        locations_time = Config.local.locations_time.get(user.language, locations='\n'.join(texts))
        return title + '\n\n'.join((total_time, max_time, locations_time)), True

    async def events_text_compile(self, user: User, campus_id: int, cursus_id: int,
                                  page: int = 0) -> Tuple[str, int, int]:
        campus = await self._get_campus(campus_id=campus_id)
        try:
            events_data = await Config.intra.get_events(campus_id=campus_id, cursus_id=cursus_id)
            exams_data = await Config.intra.get_exams(campus_id=campus_id, cursus_id=cursus_id)
            events_data.extend(exams_data)
        except (UnknownIntraError, NotFoundIntraError, TimeoutIntraError) as e:
            return f'{hbold(campus.name, ":", sep="")} {e}', 0, 0
        if not events_data:
            return Config.local.no_events.get(user.language, campus_name=campus.name), 0, 0
        events = sorted(Event().from_list(events_data=events_data),
                        key=lambda event: self._get_utc(iso_format=event.begin_at))[:10]
        count = len(events[page:])
        while True:
            if (len(events) - 1) < page:
                page -= 1
            else:
                break
        event = events[page]
        text = self.event_compile(event=event, language=user.language, time_zone=campus.time_zone)
        title = Config.local.events_title.get(user.language, campus_name=campus.name)
        return title + text, count, page

    def event_compile(self, event: Event, language: str, time_zone: str) -> str:
        duration = self._get_log_time(begin_at_iso=event.begin_at, end_at_iso=event.end_at,
                                      time_zone=time_zone, now=Config.local.now.get(language))
        location = ''
        if event.location:
            location = f'{hbold(Config.local.event_location.get(language), ":", sep="")} {event.location}\n'
        max_people = f'/{event.max_people}' if event.max_people else ''
        return self._event_cut(event_text=f'📌 {hcode(duration, f"[{event.kind}]")}\n'
                                          f'{hbold(event.name)}\n'
                                          f'{location}'
                                          f'{hbold(Config.local.event_registered.get(language), ":", sep="")} '
                                          f'{event.nbr_subscribers}{max_people}\n'
                                          f'{hitalic(event.description)}')

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
            text = '\n\n'.join((text, Config.local.donate_text_tops.get(user.language, tops=top_nicknames)))
        return text

    async def friends_list_normalization(self, user: User, current_page: int, removable: str,
                                         friends: List[PeerDB], friends_count: int) -> Tuple[str, int]:
        page = current_page
        page_data = await Cache().get(key=f'Friends:{user.id}:{page}') or []
        texts = [text for text in page_data if removable not in text.split('\n')[0]]
        texts_count = len(texts)
        if (texts_count in (0, 1) and not (page - 1)) or (not friends_count):
            await Cache().set(key=f'Friends:{user.id}:{page}', value=[])
            return Config.local.no_friends.get(user.language), 0
        if texts_count == 1 and page:
            page -= 1
            texts = await Cache().get(key=f'Friends:{user.id}:{page}')
        if friends_count >= 10:
            login = None
            text = '\n'.join(texts)
            for peer in friends[(page - 1) * 10:]:
                if peer.login not in text:
                    login = peer.login
                    break
            if login:
                _, text = await self.peer_data_compile(user=user, login=login, is_single=False)
                texts.append(text)
        from_ = (page - 1) * 10 + 1
        to = (page - 1) * 10 + texts_count - 1
        if to < friends_count:
            to = friends_count
        texts[0] = Config.local.friends_list.get(user.language, from_=from_, to=to, friends_count=friends_count)
        await Cache().set(key=f'Friends:{user.id}:{page}', value=texts)
        return '\n\n'.join(texts), page

    async def logins_separation(self, message_text: str) -> Tuple[List[str], List[str]]:
        logins = message_text.lower().replace('@', '').split()[:5]
        bad_logins = []
        logins.sort()
        logins_copy = logins.copy()
        for login in logins_copy:
            is_wrong = self._is_wrong_name(name=login)
            if is_wrong:
                logins.remove(login)
                bad_logins.append(is_wrong)
        bad_logins = list(dict.fromkeys(bad_logins))
        if len(logins) < 2:
            return logins, bad_logins
        try:
            peers = await Config.intra.get_peers(logins=logins)
        except (UnknownIntraError, TimeoutIntraError):
            return logins, bad_logins
        peer_logins = [peer['login'] for peer in peers]
        for login in logins:
            if login not in peer_logins:
                bad_logins.append(login)
        peer_logins.sort()
        return peer_logins, bad_logins


text_compile = TextCompile()

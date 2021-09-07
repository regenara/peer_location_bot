from io import BytesIO
from typing import (Any,
                    Dict,
                    List,
                    Tuple)

from bs4 import BeautifulSoup

from config import Config
from utils.intra_api import UnknownIntraError
from .text_compile import text_compile


async def logins_separation(message_text: str) -> Tuple[List[str], List[str]]:
    logins = message_text.lower().replace('@', '').split()[:5]
    bad_logins = []
    logins.sort()
    logins_copy = logins.copy()
    for login in logins_copy:
        is_wrong = text_compile.is_wrong_name(name=login)
        if is_wrong:
            logins.remove(login)
            bad_logins.append(is_wrong)
    bad_logins = list(dict.fromkeys(bad_logins))
    if len(logins) < 2:
        return logins, bad_logins
    try:
        peers = await Config.intra.get_peers(logins=logins)
    except UnknownIntraError:
        return logins, bad_logins
    peer_logins = [peer['login'] for peer in peers]
    for login in logins:
        if login not in peer_logins:
            bad_logins.append(login)
    peer_logins.sort()
    return peer_logins, bad_logins


def projects_parser(downloaded: BytesIO) -> Dict[int, Any]:
    file = BytesIO()
    file.write(downloaded.getvalue())
    file.seek(0)
    text = file.read().decode('utf-8')
    soup = BeautifulSoup(text, 'lxml')
    projects = [project for project in soup.find_all('li', class_='project-item')]
    data = {}
    for project in projects:
        courses = map(int, project.get('data-cursus').translate(str.maketrans('', '', '[ ]')).split(','))
        cursus_ids = filter(lambda cursus_id: cursus_id in Config.courses, courses)
        for cursus_id in cursus_ids:
            project_name = project.find('a').text.strip()
            data.setdefault(cursus_id, []).append(project_name)
    return data

import discord
import os
import requests
from keep_alive import keep_alive
from googlesearch import search
import re
import json
from bs4 import BeautifulSoup

client = discord.Client()


def search_anime(name):
    query = 'site:animixplay.to/v1 ' + name
    link = []
    for i in search(query, tld="co.in", num=1, stop=1, pause=1):
        link.append(i)
    if len(link) == 0:
        return 'No anime named ' + name + ' found.'
    link = link[0]
    if link.count('/') == 4:
        return link
    else:
        s = 'a'
        link = list(link)
        while s != '/':
            s = link.pop()
        link = ''.join(link)
        return link


def decode(msg):
    dic = {}
    quality = ['hdp', '360p', '480p', '720p', '1080p']
    title = re.findall("'([^']*)'", msg)
    ep = re.findall("ep[\w-]*", msg)
    if len(ep) != 0:
        ep_num = re.findall('[0-9]+', ep[0])
    else:
        ep_num = []
    qua = re.findall('[0-9hd]+p', msg)
    if len(title) == 0:
        dic['title'] = None
    else:
        dic['title'] = title[0]
    if len(ep_num) > 1:
        dic['beg'] = int(ep_num[0])
        dic['end'] = int(ep_num[1])
    elif len(ep_num) == 1:
        dic['beg'] = int(ep_num[0])
        dic['end'] = None
    else:
        dic['beg'] = None
        dic['end'] = None
    if len(qua) > 0:
        if any([qua[0] == q for q in quality]):
            dic['qua'] = qua[0]
    else:
        dic['qua'] = None
    return dic


def findids(url):
    sea = requests.get(url).text
    sea = sea.split('\n')
    ids = []
    for line in sea:
        if 'eptotal' in line:
            ids.append(line)
    print(ids)
    ids = json.loads(ids[0][:-7])
    return ids


def download(url, qua):
    QUA = qua.upper()
    id = re.findall('id=.*&', url)
    id = id[0][3:]
    url = 'https://streamani.net/download?id=' + id
    sea = requests.get(url).text
    sea = BeautifulSoup(sea, 'html.parser')
    sea = [i for i in sea.find_all('a')]
    for i in sea:
        if QUA in i.text:
            return i.get('href')
    return 'Downloadable link not found'


@client.event
async def on_message(message):
    if message.author == client.user:
        return
    if message.content.lower().startswith(
            'zoro') or message.channel.name == 'chat-with-zoro':
        msg = message.content.lower()
        msg = [wr for wr in msg.split(' ') if wr != '']
        if msg[0] == 'zoro':
            msg.pop(0)
        msg = ' '.join(msg)
        if msg.startswith('w'):
            detail = decode(msg)
            title = detail['title']
            ep = detail['beg']
            if title == None:
                await message.channel.send('where is the anime name you fool?')
            else:
                url = search_anime(detail['title'])
                ids = findids(url)
                ep_tot = ids['eptotal']
                if ep == None:
                    await message.channel.send(url)
                elif ep > ep_tot:
                    await message.channel.send('There is only ' + str(ep_tot) +
                                               ' ep released\n' + url)
                elif '-pure' in msg:
                    links = ''
                    try:
                        end = detail['end']
                        for i in range(ep, end + 1):
                            hoolink = ids[str(i - 1)]
                            if hoolink.startswith('htt'):
                                links += hoolink + '\n'
                            else:
                                links += 'https:' + hoolink + '\n'
                    except Exception:
                        hoolink = ids[str(ep - 1)]
                        if hoolink.startswith('htt'):
                            links = hoolink
                        else:
                            links = 'https:' + hoolink
                    await message.channel.send(links)
                else:
                    await message.channel.send(url + '/ep' + str(ep))
        elif msg.startswith('d'):
            detail = decode(msg)
            title = detail['title']
            ep_beg = detail['beg']
            ep_end = detail['end']
            quality = detail['qua']
            if None in [title, ep_beg]:
                await message.channel.send(
                    'Anime name and episode information needed.')
            else:
                url = search_anime(detail['title'])
                ids = findids(url)
                if ep_end == None:
                    ep_end = ep_beg + 1
                else:
                    ep_end = min(ep_end, ids['eptotal']) + 1
                if ep_beg > ids['eptotal']:
                    await message.channel.send('There is only ' +
                                               str(ids['eptotal']) +
                                               ' ep released')
                elif quality == None:
                    for i in range(ep_beg, ep_end):
                        id = re.findall('id=.*&', ids[str(i - 1)])
                        if len(id) == 0:
                            await message.channel.send(
                                'ep{} not found'.format(i))
                        else:
                            id = id[0][3:]
                            await message.channel.send(
                                'ep{} https://streamani.net/download?id={}\n'.
                                format(i, id))
                else:
                    for i in range(ep_beg, ep_end):
                        await message.channel.send('ep{} {} {}\n'.format(
                            i, quality, download(ids[str(i - 1)], quality)))


keep_alive()
client.run(os.environ['TOKEN'])

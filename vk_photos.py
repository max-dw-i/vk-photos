"""Download the photos from a user, group vk.com page or album.

usage: vk_photos.py [-h] [-a ALBUM] [-u USER_PAGE] [-g GROUP_PAGE] [-m] [-s]
                    [-sw] [-sp] [-ss] [-t]
                    username password path

positional arguments:
    username                                 VK login
    password                                 VK password
    path                                     directory where you want to save the photos

optional arguments:
    -h, --help                               show this help message and exit
    -a ALBUM, --album ALBUM                  link to an album page
                                             (e.g. https://vk.com/album11111_111111111)
    -u USER_PAGE, --user_page USER_PAGE      link to a user page (e.g. https://vk.com/id1)
    -g GROUP_PAGE, --group_page GROUP_PAGE   link to a group page (e.g. https://vk.com/club1)
    -m, --main                               download the group/user albums
    -s, --system_all                         download the system albums
    -sw, --system_wall                       download the photos from the wall (system album)
    -sp, --system_profile                    download the profile photos (system album)
    -ss, --system_saved                      download the saved photos (system album)
    -t, --tagged                             download the photos the user is tagged on


For example, to get all the photos from a user page (https://vk.com/id1) (all the albums,
including system and 'tagged') and save them in 'C:\photos' (your VK login is 'mail@mail.com'
and VK password is 'mypass'):

>> python vk_photos.py mail@mail.com mypass C:\photos -u https://vk.com/id1 -m -s -t

"""

import argparse
import datetime
import os
import sys
import time

import requests
import vk_api


def download_album(connection, output_path, owner_id, album_title, album_size, album_id=0, tagged=True):
    """Create a directory and get an album with VK API.

    Parameters:
    -----------
    :connection: connection object, vk_api.VkApi(...) instance;
    :output_path: str, path where to save the photos;
    :owner_id: int, id of the group/user;
    :album_title: str, the album title;
    :album_size: int, number of photos in the album;
    :album_id: int, id of the album or 0 if it's the album with 'tagged' photos;
    :tagged: bool, True if the album is the one with the photos the user has been tagged on.
    """

    album_dir = del_restricted_symbols(album_title)

    output_dir = os.path.join(output_path, album_dir)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # We can't get more than 1000 photos in one response so we're going to use
    # 'count' and 'offset' parameters
    for offset in range(album_size//MAX_PHOTO_NUM+1):
        if tagged:
            photos_list = connection.method(
                'photos.getUserPhotos',
                {'user_id': owner_id, 'count': MAX_PHOTO_NUM, 'offset': offset*MAX_PHOTO_NUM}
            )
        else:
            photos_list = connection.method(
                'photos.get',
                {'owner_id': owner_id, 'album_id': album_id, 'count': MAX_PHOTO_NUM,
                 'offset': offset*MAX_PHOTO_NUM}
            )

        download_photos(photos_list['items'], output_dir, offset)

def download_photos(photos, output_path, offset):
    """Download the photos we get from VK API response.

    Parameters:
    -----------
    :photos: list containing VK API 'photo objects' (a dictionaries);
    :output_path: path where to save the photos;
    :offset: VK API 'offset' parameter.
    """

    for i, photo in enumerate(photos):
        progress = "\rDownloading...{}".format(offset*MAX_PHOTO_NUM+i+1)
        sys.stdout.write(progress)
        sys.stdout.flush()

        # We can meet a deleted photo in an album so, if it's the case,
        # go to the next photo
        if not photo['sizes']: continue

        # Get all the resolutions of the photo existed
        photo_links = {size['type']: size['url'] for size in photo['sizes']}

        # Get the url of the photo with the max resolution
        for photo_type in 'wzyxrqpmos':
            url = photo_links.get(photo_type)
            if url: break

        photo_date = datetime.datetime.fromtimestamp(photo['date']).strftime('%Y%m%d@%H%M')
        photo_title = '{}_{}'.format(photo_date, photo['id'])

        p = requests.get(url, timeout=None)

        with open(os.path.join(output_path, '{}.jpg'.format(photo_title)), 'wb') as f:
            f.write(p.content)

def get_album_size(connection, owner_id, album_id=0, tagged=True):
    """Returns the size of an album.

    Parameters:
    -----------
    :connection: connection object, vk_api.VkApi(...) instance;
    :owner_id: int, id of the group/user;
    :album_id: int, id of the album or 0 if it's the album with 'tagged' photos;
    :tagged: bool, True if the album is the one with the photos the user has been tagged on;
    :returns: int, number of photos in the album
    """

    if tagged:
        photos_list = connection.method('photos.getUserPhotos', {'user_id': owner_id})
    else:
        photos_list = connection.method('photos.get', {'owner_id': owner_id, 'album_id': album_id})

    return photos_list['count']

def del_restricted_symbols(album_title):
    """Returns the name of the directory without the restricted symbols.

    Parameters:
    -----------
    :album_title: str, name of the album;
    :returns: str, name of the directory
    """

    # Symbols that are not allowed in Windows dir names
    # Change title to prevent exceptions during download
    sym_replace = {'"', ':', '&', '.', '|', '\\', '/', '*', '?', '<', '>'}
    title = album_title.strip()

    for s in title:
        if s in sym_replace:
            title = '-'.join(title.split(s))

    return title

def get_owner_id(connection, screen_name, user=False):
    """Get the owner id of a user or group page.

    Parameters:
    -----------
    :connection: connection object, vk_api.VkApi(...) instance;
    :screen_name: str, name of a user or group page we get from a link
    (e.g. https://vk.com/azino777, azino777 is the screen name);
    :user: bool, True if it's a user page, False if it's a group page;
    :returns: int, the owner id
    """

    if user:
        # Get a list of user objects (in our case, one object)
        user_objs = connection.method('users.get', {'user_ids': screen_name})
        # Get the id of the user
        return user_objs[0]['id']
    else:
        # Get a list of group objects (in our case, one object)
        group_objs = connection.method('groups.getById', {'group_id': screen_name})
        # Get the id of the group (an id must be negative if it's a group)
        return group_objs[0]['id'] * (-1)

def arg_handler(args):
    """Form a dictionary with all the parameters to do VK API queries.

    Parameters:
    -----------
    :args: argparse.Namespace object;
    :returns: dictionary {'username': str, VK login, 'password': str, VK password,
                          'output_dir': str, directory to save photos in,
                          'page': str, 'album' or 'user' or 'group',
                          'link': str, link to a album/user/group page,
                          'main': bool, group/user albums,
                          'system_wall': bool, photos from the wall,
                          'system_profile: bool, profile photos,
                          'system_saved': bool, saved by user/group photos,
                          'tagged': bool, photos the user is tagged on}
    """

    params = {'username': args.username,
              'password': args.password,
              'output_dir': args.path}

    if not args.album and not args.user_page and not args.group_page:
        raise Exception("There is no page/album link")

    main_system_chosen = (args.main or args.system_all or args.system_profile or
                          args.system_saved or args.system_wall or args.tagged)

    if ((args.user_page and not (main_system_chosen or args.tagged)) or
            (args.group_page and not main_system_chosen)):
        raise Exception("Choose album types to download")

    if args.tagged and not args.user_page:
        raise Exception("Cannot download 'tagged' photos for an album or a group")

    if args.album and not args.user_page and not args.group_page:
        params['page'] = 'album'
        params['link'] = args.album
    elif not args.album and args.user_page and not args.group_page:
        params['page'] = 'user'
        params['link'] = args.user_page
    elif not args.album and not args.user_page and args.group_page:
        params['page'] = 'group'
        params['link'] = args.group_page
    else:
        raise Exception("Choose just one page type")

    params['main'] = args.main
    params['tagged'] = args.tagged
    params['system_wall'] = args.system_wall
    params['system_profile'] = args.system_profile
    params['system_saved'] = args.system_saved

    if args.system_all:
        params['system_wall'] = True
        params['system_profile'] = True
        params['system_saved'] = True

    return params

def link_parse(link, page):
    """Returns the owner and album ids for an album or the screen name of either
    user or group page.

    Parameters:
    -----------
    :link: str, e.g. https://vk.com/album11111_111111111 or https://vk.com/club1;
    :page: str, one of {'album', 'user', 'group'};
    :returns: str or tuple of ints, e.g. 'club1' or (11111, 111111111)
    """

    link_end = link.split('/')[-1]

    if page == 'album':
        ids = link_end.split('album')[1].split('_')
        return int(ids[0]), int(ids[1])
    else:
        return link_end


if __name__ == '__main__':

    # ---------------------------------------------------------
    # VK API returns only 1000 photos in one response (at least now)
    MAX_PHOTO_NUM = 1000
    # ---------------------------------------------------------

    # Parse the arguments
    parser = argparse.ArgumentParser(
        description="Download the photos from a user, group vk.com page or album."
    )
    parser.add_argument('username', help="VK login")
    parser.add_argument('password', help="VK password")
    parser.add_argument('path', help="directory where you want to save the photos")
    parser.add_argument('-a', '--album',
                        help="link to an album page (e.g. https://vk.com/album11111_111111111)")
    parser.add_argument('-u', '--user_page',
                        help="link to a user page (e.g. https://vk.com/id1)")
    parser.add_argument('-g', '--group_page',
                        help="link to a group page (e.g. https://vk.com/club1)")
    parser.add_argument('-m', '--main', action='store_true', default=False,
                        help="download the group/user albums")
    parser.add_argument('-s', '--system_all', action='store_true', default=False,
                        help="download the system albums")
    parser.add_argument('-sw', '--system_wall', action='store_true', default=False,
                        help="download the photos from the wall (system album)")
    parser.add_argument('-sp', '--system_profile', action='store_true', default=False,
                        help="download the profile photos (system album)")
    parser.add_argument('-ss', '--system_saved', action='store_true', default=False,
                        help="download the saved photos (system album)")
    parser.add_argument('-t', '--tagged', action='store_true', default=False,
                        help="download the photos the user is tagged on")
    args = parser.parse_args()

    args_dict = arg_handler(args)

    if not os.path.exists(args_dict['output_dir']):
        os.makedirs(args_dict['output_dir'])

    try:
        connection = vk_api.VkApi(args_dict['username'], args_dict['password'])
        connection.auth()

        if args_dict['page'] == 'album':
            owner_id, album_id = link_parse(args_dict['link'], args_dict['page'])
            album_size = get_album_size(connection, owner_id, album_id, False)
            print('\n{}. Num of photos: {}.'.format('Album', album_size))
            download_album(connection, args_dict['output_dir'], owner_id,
                           'Album', album_size, album_id, False)
        else:
            screen_name = link_parse(args_dict['link'], args_dict['page'])

            if args_dict['page'] == 'user':
                owner_id = get_owner_id(connection, screen_name, True)
            else:
                owner_id = get_owner_id(connection, screen_name, False)

            if args_dict['main']:
                try:
                    albums = connection.method('photos.getAlbums', {'owner_id': owner_id})

                    for album in albums['items']:
                        print('\n{}. Num of photos: {}.'.format(album['title'], album['size']))
                        download_album(connection, args_dict['output_dir'], owner_id,
                                       album['title'], album['size'], album['id'], False)

                        # VK API allows to do 3 queries per sec
                        time.sleep(1)

                except vk_api.exceptions.ApiError as vk_e:
                    print('\n(--main) album', vk_e)

            if args_dict['page'] == 'user' and args_dict['tagged']:
                try:
                    album_size = get_album_size(connection, owner_id)
                    print('\n{}. Num of photos: {}.'.format('Photos the user is tagged on', album_size))
                    download_album(connection, args_dict['output_dir'], owner_id,
                                   'Photos the user is tagged on', album_size)

                    time.sleep(1)

                except vk_api.exceptions.ApiError as vk_e:
                    print('\n(--tagged) album', vk_e)

            if args_dict['system_wall']:
                try:
                    album_size = get_album_size(connection, owner_id, 'wall', False)
                    print('\n{}. Num of photos: {}.'.format('Photos from the wall', album_size))
                    download_album(connection, args_dict['output_dir'], owner_id,
                                   'Photos from the wall', album_size, 'wall', False)

                    time.sleep(1)

                except vk_api.exceptions.ApiError as vk_e:
                    print('\n(--system_wall) album', vk_e)

            if args_dict['system_profile']:
                try:
                    album_size = get_album_size(connection, owner_id, 'profile', False)
                    print('\n{}. Num of photos: {}.'.format('Profile photos', album_size))
                    download_album(connection, args_dict['output_dir'], owner_id,
                                   'Profile photos', album_size, 'profile', False)

                    time.sleep(1)

                except vk_api.exceptions.ApiError as vk_e:
                    print('\n(--system_profile) album', vk_e)

            if args_dict['system_saved']:
                try:
                    album_size = get_album_size(connection, owner_id, 'saved', False)
                    print('\n{}. Num of photos: {}.'.format('Saved photos', album_size))
                    download_album(connection, args_dict['output_dir'], owner_id,
                                   'Saved photos', album_size, 'saved', False)
                except vk_api.exceptions.ApiError as vk_e:
                    print('\n(--system_saved) album', vk_e)

    except vk_api.exceptions.ApiError as vk_e:
        print(vk_e)

    except KeyboardInterrupt:
        print('\nStopped by the user.')
        sys.exit()

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(e)
        print(exc_type, fname, exc_tb.tb_lineno)
        sys.exit(1)

    finally:
        print("\nDone.")

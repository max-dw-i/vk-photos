# VK Photos

A script downloading the photographs from a user or group page or any particular album on vk.com.

## Features

You can:

* Download any album;
* Download all the albums from a user or group page;
* Download different album types separately (e.g. wall photos and 'main' albums).

## Installing

You need Python 3.* to be installed. Then:

```bash
# Go to the dir you want to save the script in
cd C:\vk_photos
# Clone the repository
git clone git@github.com:oratosquilla-oratoria/vk-photos.git
# Install the requirements
pip install -r requirements.txt
```

## Usage

```
vk_photos.py [-h] [-m] [-s] [-sw] [-sp] [-ss] [-t]
                    username password path {album,group,user} link

positional arguments:
  username              VK login
  password              VK password
  path                  directory where you want to save the photos
  {album,group,user}    page type
  link                  link to an album, user page or group page (e.g.
                        https://vk.com/album11111_111111111 or
                        https://vk.com/id1)

optional arguments:
  -h, --help            show this help message and exit
  -m, --main            download the group/user albums
  -s, --system_all      download the system albums
  -sw, --system_wall    download the photos from the wall (system album)
  -sp, --system_profile
                        download the profile photos (system album)
  -ss, --system_saved   download the saved photos (system album)
  -t, --tagged          download the photos the user is tagged on
```

You'll get all the photos from the page if you don't use any positional
arguments.

For example, to get all the photos from a user page (https://vk.com/id1) (all the albums,
including system and 'tagged') and save them in 'C:\photos' (let 'mail@mail.com' and 'mypass'
be your login and password):
```bash
python vk_photos.py mail@mail.com mypass C:\photos user https://vk.com/id1
```
or
```bash
python vk_photos.py mail@mail.com mypass C:\photos user https://vk.com/id1 -m -s -t
```
These two are the same.
If you want to get, for instance, only the wall photos and 'tagged', then:
```bash
python vk_photos.py mail@mail.com mypass C:\photos user https://vk.com/id1 -sw -t
```

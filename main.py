import json
import os
from datetime import datetime
from pprint import pprint
import requests
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from tqdm import tqdm


# Класс для взаимодействия с VK
class VK:
    def __init__(self, vk_token, version='5.199'):
        self.params = {
            'access_token': vk_token,
            'v': version
        }
        self.base_url = 'https://api.vk.com/method/'

    # Выбор пользователем альбома
    def get_name_album(self):
        album = ''
        if album_vk == '1':
            album = 'profile'
        elif album_vk == '2':
            album = 'wall'
        return album

    # Получение фото из VK
    def get_photos(self, user_id, count = 5):
        album = self.get_name_album()
        url = f'{self.base_url}photos.get'
        params = {
                'owner_id': user_id,
                'count': count,
                'album_id': album,
                'extended': 1
            }

        params.update(self.params)
        response = requests.get(url, params=params)
        data = response.json()
        photos = []

        for i, item in enumerate(data['response']['items']):  # Ищем наибольшее разрешение у каждого фото
            max_type = ''
            for size in item['sizes']:
                if size['type'] == 'w':
                    max_type = size['type']
                    break
                match size['type']:
                    case 'z':
                        max_type = size['type']
                    case 'y':
                        max_type = size['type']
                    case 'r':
                        max_type = size['type']
                    case 'q':
                        max_type = size['type']
                    case 'p':
                        max_type = size['type']
                    case 'o':
                        max_type = size['type']
                    case 'x':
                        max_type = size['type']
                    case 'm':
                        max_type = size['type']
                    case 's':
                        max_type = size['type']

            for size in item['sizes']:  # отбираем в наибольшем разрешении и добавляем в список вместе с кол-м лайков
                if size['type'] == max_type:
                    photos.append(
                        {'date': datetime.fromtimestamp(item['date']), 'likes': item['likes']['count'],
                         'size': size['type'],
                         'url': size['url']})

        for photo in photos:   # Если лайки есть, то название фото будет кол-во лайков, если нет, то названием будет дата
            if photo['likes']  >= 1:
                photo['file_name'] = f'{photo['likes']}.jpg'
            else:
                photo['file_name'] = f'{photo['date'].strftime('%d.%m.%y_%H:%M:%S')}.jpg'

        return photos

# Класс для взаимодействия с ЯД
class YD:
    def __init__(self, yd_token, version='v1'):
        self.headers = {
            'Authorization': yd_token
        }
        self.params = {
            'v': version
        }
        self.base_url = 'https://cloud-api.yandex.net'

    # Создание папки на ЯД
    def create_folder(self):
        params = {
            'path': 'VK'
        }
        params.update(self.params)
        url = f'{self.base_url}/v1/disk/resources'

        if requests.get(url, headers=self.headers, params=params).status_code != 201: # Проверка наличия папки
            requests.put(url, headers=self.headers, params=params)

    # Загрузка фото на ЯД
    def upload_photos(self, upload_file):
        self.create_folder()
        for item in tqdm(upload_file):
            pprint(item['file_name'])
            params = {
                'path': f'VK/{item['file_name']}',
                'url': item['url']
            }
            params.update(self.params)
            url = f'{self.base_url}/v1/disk/resources/upload'
            requests.post(url, headers=self.headers, params=params)

# Класс взаимодействия с GD
class GD:
    def gd_auth(self):
        self.creds = None
        SCOPES = ['https://www.googleapis.com/auth/drive']
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES
                )
                self.creds = flow.run_local_server(port=0)

    # Создание папки на GD
    def create_folder(self):
        service = build('drive', 'v3', credentials=self.creds)
        file_metadata = {
            'name': 'VK',
            'mimeType': 'application/vnd.google-apps.folder',
            }
        service.files().create(body=file_metadata, fields='id').execute()
        response = (service.files().list(q="name contains 'VK'", spaces='drive', fields='files(id)').execute())
        folder_id = response['files']['id']
        return folder_id

    # Проверна наличия папки на GD
    def chek_folder_name(self):
        # Проверка наличия папки
        self.gd_auth()
        service = build('drive', 'v3', credentials=self.creds)
        response = (service.files().list(q="name contains 'VK'", spaces='drive', fields='files(id)').execute())
        if len(response['files']) == 0:
            self.create_folder()

    # Загрузка фото на GD
    def upload_photos(self, upload_file):
        self.chek_folder_name()
        # Получаем id папки для загрузки
        folder_for_upload = []
        service = build('drive', 'v3', credentials=self.creds)
        response = (service.files().list(q="name contains 'VK'", spaces='drive', fields='files(id)').execute())
        folder_for_upload.extend(response.get('files', []))
        folder_id = folder_for_upload[0]['id']

        # Скачиваем фото на компьютер
        os.chdir('VK')
        for photo in tqdm(upload_file):
            file_name = photo['file_name']
            photo_url = photo['url']
            response = requests.get(photo_url)
            with open(file_name, 'wb') as file:
                file.write(response.content)
                service = build('drive', 'v3', credentials=self.creds)
                file_metadata = {
                'name': file_name,
                'parents': [folder_id]
                }
                media = MediaFileUpload(photo['file_name'], mimetype='image/jpeg')
                response = (service.files().create(body=file_metadata, media_body=media, fields='id').execute())

vk_token = input(f'Введите токен для VK: ')
vk_user_id = input(f'Введите ID пользователя VK: ')
album_vk = input(f'Введите цифру, которая соответсвует альбому откуда '
                 f'Вы хотите скопировать фото: 1 - фотографии профиля, '
                 f'2 - фотографии со стены: ')

while album_vk != '1' or album_vk != '2':
    if album_vk == '1' or album_vk == '2':
        print('Альбом выбран')
        break
    else:
        print('Вы можете ввести только 1 или 2')
        album_vk = input(f'Введите цифру, которая соответсвует альбому откуда '
                         f'Вы хотите скопировать фото: 1 - фотографии профиля, '
                         f'2 - фотографии со стены : ')

vk_connector = VK(vk_token)
photos_data = vk_connector.get_photos(vk_user_id)

# Формируем json и список для загрузки на ЯД
json_file = []
upload_file = []

for item in photos_data:
    json_file.append({'file_name': item['file_name'], 'size': item['size']})
    upload_file.append({'file_name': item['file_name'], 'url': item['url']})

with open('photo_data.json', 'w') as f:
    json.dump(json_file, f, ensure_ascii=False, indent=2)

disk = input(f'Выберите куда загрузить фотографии: 1 - Яндекс диск, 2 - Гугл диск: ')

while disk != '1' or disk != '2':
    if disk == '1' or disk == '2':
        print('Место загрузки выбрано')
        break
    else:
        print('Вы можете ввести только 1 или 2')
        album_vk = input(f'Выберите куда загрузить фотографии: 1 - Яндекс диск, 2 - Гугл диск')

if disk == '1':
    yd_token = input(f'Введите токен для Яндекс диска: ')
    yd_connector = YD(yd_token)
    yd_connector.upload_photos(upload_file)
elif disk == '2':
    gd_connector = GD()
    gd_connector.upload_photos(upload_file)






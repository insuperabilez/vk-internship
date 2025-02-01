import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.upload import VkUpload
from vk_api.utils import get_random_id
import os
import random
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

TOKEN='ваш токен'

def upload_photo(upload, photo_path):
    with open(photo_path, 'rb') as photo_file:
        response = upload.photo_messages(photo_file)[0]
    owner_id = response['owner_id']
    photo_id = response['id']
    access_key = response['access_key']
    return owner_id, photo_id, access_key


def send_photos(vk, peer_id, attachments_list):
    attachment_str = ",".join(attachments_list)
    vk.messages.send(
        random_id=get_random_id(),
        peer_id=peer_id,
        attachment=attachment_str
    )


def main():
    vk_session = vk_api.VkApi(token=TOKEN)
    vk = vk_session.get_api()
    upload = VkUpload(vk)
    longpoll = VkLongPoll(vk_session)
    greeted_users = set()
    logging.info("Бот запущен и ждёт сообщений...")
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            user_id = event.user_id
            if user_id not in greeted_users:
                try:
                    vk.messages.send(
                        user_id=user_id,
                        message="Добро пожаловать!",
                        random_id=get_random_id()
                    )
                    greeted_users.add(user_id)
                    logging.info(f"Приветственное сообщение отправлено пользователю {user_id}")
                except Exception as e:
                    logging.error(f"Ошибка при отправке приветственного сообщения пользователю {user_id}: {e}")
            attachments = vk.messages.getById(message_ids=event.message_id)['items'][0]['attachments']
            photo_attachments = []
            temp_files = []
            index = 0
            for attach in attachments:
                if attach['type'] == 'photo':
                    photo = attach['photo']
                    sizes = photo.get('sizes', [])
                    if not sizes:
                        continue
                    photo_url = sizes[-1]['url']
                    file_name = f"received_photo_{index}.jpg"
                    index += 1
                    temp_files.append(file_name)
                    try:
                        photo_content = vk_session.http.get(photo_url).content
                        with open(file_name, 'wb') as f:
                            f.write(photo_content)
                    except Exception as e:
                        logging.error(f"Ошибка при сохранении фото: {e}")
                        continue
                    try:
                        owner_id, photo_id, access_key = upload_photo(upload, file_name)
                        attachment = f'photo{owner_id}_{photo_id}_{access_key}'
                        photo_attachments.append(attachment)
                    except Exception as e:
                        logging.error(f"Ошибка при загрузке фото: {e}")
                        continue
            if photo_attachments:
                try:
                    send_photos(vk, user_id, photo_attachments)
                    logging.info(f"Фото отправлены пользователю {user_id}")
                except Exception as e:
                    logging.error(f"Ошибка при отправке фото: {e}")
            else:
                logging.info(f"У пользователя {user_id} не найдено фото во вложениях.")
            for file in temp_files:
                try:
                    os.remove(file)
                    logging.info(f"Удалён файл {file}")
                except Exception as e:
                    logging.error(f"Ошибка при удалении файла {file}: {e}")


if __name__ == '__main__':
    main()

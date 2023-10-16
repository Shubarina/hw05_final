# Соцсеть Yatube
Социальная сеть микроблогов, в которой можно публиковать посты в своем блоге или в отдельной группе, комментировать посты, подписываться на любимых авторов.  
Для проекта написаны тесты Unittest.

### Как запустить проект локально:
1. Клонировать репозиторий:
```
git clone git@github.com:Shubarina/hw05_final.git
```
2. Создать и активировать виртуальное окружение, обновить пакетный менеджер и установить зависимости из файла requirements.txt::
```
python3 -m venv env
source env/scripts/activate
python3 -m pip install --upgrade pip
pip install -r requirements.txt
```
3. Выполнить миграции и запустить проект:
```
python3 manage.py migrate
python3 manage.py runserver
```

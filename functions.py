import hashlib
import random
from flask import Flask, request, jsonify, make_response, redirect
from flask_jwt_extended import jwt_manager, create_access_token, get_jwt_identity, jwt_required


# РЕГИСТРАЦИЯ ПОЛЬЗОВАТЕЛЯ
def register_user(database, Users):
    if request.method == "POST":
        login = str(request.json["login"]).strip()
        password = str(request.json["password"]).strip()

        if login == "":
            return make_response("Введите логин!")
        elif password == "":
            return make_response("Введите пароль!")
        elif login == "" and password == "":
            return make_response("Введите логин и пароль!")

        elif Users.query.filter_by(login=request.json["login"]).first() is None:
            database.session.add(Users(login=request.json["login"], password=request.json["password"]))
            database.session.commit()
            return make_response("Вы успешно зарегистрировались!")
        else:
            return make_response("Вы уже зарегистрировались!")

    else:
        return {"OK": True}


# АВТОРИЗАЦИЯ ПОЛЬЗОВАТЕЛЯ
def auth_user(database, Users):
    if request.method == "POST":
        login = str(request.json["login"]).strip()
        password = str(request.json["password"]).strip()
        database_password = database.session.execute(database.select(Users.password).filter_by(login=login)).first()[0]

        if Users.query.filter_by(login=login).first() is not None:
            if password == database_password:
                return make_response(f"Вы вошли в систему: {create_access_token(identity=login)}")
            else:
                return make_response("Неправильный пароль")
        else:
            return make_response("Неправильный логин")

    else:
        return {"OK": True}


# ДОБАВИТЬ ССЫЛКУ БУДУЧИ АВТОРИЗОВАННЫМ
def add_link_auth(database, Links, Users):
    if request.method == "POST":
        login = get_jwt_identity()
        alias = request.json["alias"]
        long_link = request.json["long_link"]
        access = request.json["access"]
        short_link = hashlib.md5(long_link.encode()).hexdigest()[:random.randint(8, 12)]
        user_id = database.session.execute(database.select(Users.id).filter_by(login=login)).first()[0]
        all_link = Links.query.filter_by(alias=alias)

        if all_link is None:
            if alias == "":
                database.session.add(
                    Links(user_id=user_id, long_link=long_link, short_link=short_link, access_level=access))
                database.session.commit()

                return make_response("Ваша короткая ссылка - " + short_link + ". Никнейм можно будет задать позднее.")
            else:
                database.session.add(Links(user_id=user_id, long_link=long_link, short_link=short_link, alias=alias,
                                           access_level=access))
                database.session.commit()

                return make_response("Ваша короткая ссылка с ипользованием никнейма - " + alias + ".")

        return make_response("Введите другой никнейм, потому что этот уже занят!")
    else:
        return {"OK": True}


# ДОБАВИТЬ ССЫЛКУ БУДУЧИ НЕАВТОРИЗОВАННЫМ
def add_link_unauth():
    if request.method == "POST":
        long_link = request.json["long_link"]
        short_link = hashlib.md5(long_link.encode()).hexdigest()[:random.randint(8, 12)]

        return make_response("Короткая ссылка - " + short_link)

    else:
        return {"OK": True}


# ФУНКЦИЯ ДЛЯ РЕДИРЕКТА ПО КОРОТКОЙ ССЫЛКЕ
def counting_by_short(database, Links):
    link_by_short = database.session.execute(
        database.select(Links.long_link, Links.access_level, Links.count, Links.alias).filter_by(
            short_link=request.json["short_link"])).first()

    if link_by_short is not None:
        if link_by_short[1] == 1:
            if link_by_short[2] is None:
                count = 1
            else:
                count = link_by_short[1] + 1

            Links.query.filter_by(long_link=link_by_short[0]).update({"count": count})
            database.session.commit()
            return redirect(link_by_short[0])

        if link_by_short[1] == 2:
            login = get_jwt_identity()

            if login is not None:
                if link_by_short[2] is None:
                    count = 1
                else:
                    count = link_by_short[1] + 1

                Links.query.filter_by(long_link=link_by_short[0]).update({"count": count})
                database.session.commit()
                return redirect(link_by_short[0])

            else:
                return make_response("Вы не авторизованы.")


# ФУНКЦИЯ ДЛЯ РЕДИРЕКТА ПО НИКНЕЙМУ
def counting_by_alias(database, Links):
    link_by_alias = database.session.execute(
        database.select(Links.long_link, Links.access_level, Links.count, Links.alias).filter_by(
            alias=request.json["alias"])).first()

    if link_by_alias is not None:
        if link_by_alias[1] == 1:
            if link_by_alias[2] is None:
                count = 1
            else:
                count = link_by_alias[1] + 1

            Links.query.filter_by(long_link=link_by_alias[0]).update({"count": count})
            database.session.commit()
            return redirect(link_by_alias[0])

        if link_by_alias[1] == 2:
            login = get_jwt_identity()

            if login is not None:
                if link_by_alias[2] is None:
                    count = 1
                else:
                    count = link_by_alias[1] + 1

                Links.query.filter_by(long_link=link_by_alias[0]).update({"count": count})
                database.session.commit()
                return redirect(link_by_alias[0])
            else:
                return make_response("Вы не авторизованы.")


# РЕДИРЕКТ
def counting(database, Links):
    if request.method == "POST":
        link_by_short = database.session.execute(
            database.select(Links.long_link, Links.access_level, Links.count, Links.alias).filter_by(
                short_link=request.json["short_link"])).first()
        link_by_alias = database.session.execute(
            database.select(Links.long_link, Links.access_level, Links.count, Links.alias).filter_by(
                alias=request.json["alias"])).first()

        if link_by_short is not None:
            return counting_by_short(database, Links)
        elif link_by_alias is not None:
            return counting_by_alias(database, Links)
        else:
            return make_response("Невозможно совершить действие.")
    else:
        return {"OK": True}


# РЕДАКТИРОВАНИЕ ССЫЛКИ
def edit_link(database, Links, Users, link):
    if request.method == "POST":
        login = get_jwt_identity()
        alias = request.json["alias"]
        user_id = database.session.execute(database.select(Users.id).filter_by(login=login)).first()[0]

        searched_link_1 = database.session.execute(
            database.select(Links.long_link, Links.short_link, Links.access_level, Links.count, Links.alias).filter_by(
                short_link=link)).first()
        searched_link_2 = database.session.execute(
            database.select(Links.long_link, Links.access_level, Links.count, Links.alias).filter_by(
                alias=link)).first()
        all_link = Links.query.filter_by(alias=alias)

        if all_link is None:
            if searched_link_1[1] == link:
                Links.query.filter_by(user_id=user_id, short_link=link).update(
                    {"access_level": request.json["access_level"], "alias": alias})
                database.session.commit()

                return make_response("Ссылка обновлена!")

            elif searched_link_2[3] == link:
                Links.query.filter_by(user_id=user_id, alias=link).update(
                    {"alias": alias, "access_level": request.json["access_level"]})
                database.session.commit()

                return make_response("Ссылка обновлена!")

            else:
                return make_response("Ваша ссылка не найдена.")

        else:
            return make_response("Введите короткую ссылку или проверьте никнейм.")

    else:
        return {"OK": True}


# УДАЛЕНИЕ ССЫЛКИ
def delete_link(database, Links, Users):
    login = get_jwt_identity()
    user_id = database.session.execute(database.select(Users.id).filter_by(login=login)).first()[0]

    searched_link_1 = database.session.execute(
        database.select(Links.long_link, Links.short_link, Links.access_level, Links.count, Links.alias).filter_by(
            short_link=request.json["short_link"])).first()
    searched_link_2 = database.session.execute(
        database.select(Links.long_link, Links.access_level, Links.count, Links.alias).filter_by(
            alias=request.json["alias"])).first()

    if searched_link_1 is not None:
        Links.query.filter_by(user_id=user_id, short_link=request.json["short_link"]).delete()
        database.session.commit()

        return make_response("Ссылка успешно удалена!")

    elif searched_link_2 is not None:
        Links.query.filter_by(user_id=user_id, alias=request.json["alias"]).delete()
        database.session.commit()

        return make_response("Ссылка успешно удалена!")

    else:
        return make_response("Не удалось удалить ссылку.")

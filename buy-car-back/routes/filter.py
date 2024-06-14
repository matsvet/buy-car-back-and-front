from bson import ObjectId
from app import app, db
from flask import jsonify, request


@app.route('/filter', methods=['GET'])
def get_filter():
    # Получаем userId из строки запроса
    user_id = request.args.get('userId')

    if not user_id:
        return jsonify({'error': 'userId required'}), 400

    # Ищем фильтр по userId
    # Предполагается, что userId хранится в виде строки, если нет - возможно, потребуется преобразование
    item = db.filter.find_one({'userId': user_id})

    if not item:
        # return jsonify({'error': 'Filter was not found'}), 404
        return jsonify(None)

    # Формируем результат
    result = {
        'id': str(item['_id']),
        'userId': item['userId'],
        'priceMin': item.get('priceMin', None),
        'priceMax': item.get('priceMax', None),
        'mileageMin': item.get('mileageMin', None),
        'mileageMax': item.get('mileageMax', None),
        'yearMin': item.get('yearMin', None),
        'yearMax': item.get('yearMax', None),
        'ownersCountMin': item.get('ownersCountMin', None),
        'ownersCountMax': item.get('ownersCountMax', None),
        'mark': item.get('mark', None),
        'model': item.get('model', None),
        'settlement': item.get('settlement', None),
        'isShowroom': item.get('isShowroom', None),
        'sorting': item.get('sorting', None),
    }

    return jsonify(result)

@app.route('/filter', methods=['PUT'])
def update_or_create_filter():
    # Получаем данные из тела запроса
    data = request.json
    user_id = data.get('userId')
    
    if not user_id:
        return jsonify({'error': 'userId required'}), 400

    # Создаем объект для обновления, исключая 'userId' для обновления
    update_data = {
        'priceMin': data.get('priceMin', None),
        'priceMax': data.get('priceMax', None),
        'mileageMin': data.get('mileageMin', None),
        'mileageMax': data.get('mileageMax', None),
        'yearMin': data.get('yearMin', None),
        'yearMax': data.get('yearMax', None),
        'ownersCountMin': data.get('ownersCountMin', None),
        'ownersCountMax': data.get('ownersCountMax', None),
        'mark': data.get('mark', None),
        'model': data.get('model', None),
        'settlement': data.get('settlement', None),
        'isShowroom': data.get('isShowroom', None),
        'sorting': data.get('sorting', None),
    }

    # Удаляем ключи, значения которых None
    # update_data = {k: v for k, v in update_data.items() if v is not None}

    # Обновляем документ в коллекции или создаем новый, если он не найден
    result = db.filter.update_one({'userId': user_id}, {'$set': update_data}, upsert=True)

    if result.upserted_id:
        return jsonify({'message': 'Фильтр создан', 'id': str(result.upserted_id), 'filterData': update_data}), 201
    else:
        return jsonify({'message': 'Фильтр обновлен', 'filterData': update_data}), 200

# Марки для Select
@app.route('/filter/marks', methods=['GET'])
def get_filterMarks():
    # Агрегация для получения уникальных значений поля "Марка"
    unique_marks = db.marksAndModels.aggregate([
         # Сортировка по "Популярная марка" (true > false) и алфавиту
        {"$sort": {"Популярная марка": -1, "Марка": 1}},
        # Группировка уникальных значений "Марка" с сохранением значения "Популярная марка"
        {"$group": {"_id": "$Марка", "Популярная марка": {"$first": "$Популярная марка"}}},
        # Сортировка группированных значений сначала по "Популярная марка" для сохранения порядка и по "_id" для алфавитной сортировки внутри групп
        {"$sort": {"Популярная марка": -1, "_id": 1}}
    ])
    
    # Преобразование результатов в список
    result = [mark['_id'] for mark in unique_marks]
    
    return jsonify(result)

# Модели для Select в зависимости от марки
@app.route('/filter/models', methods=['GET'])
def get_filterModels():
    mark = request.args.get('mark')

    if not mark:
        return jsonify({'error': 'mark required'}), 400

    models = db.marksAndModels.find({"Марка": mark}, {"Модель": 1, "_id": 0})

    models_list = [model['Модель'] for model in models]

    return jsonify(models_list)

# Города для Select
@app.route('/filter/cities', methods=['GET'])
def get_filter_cities():
    # Используем агрегацию для получения уникальных и отсортированных значений городов
    pipeline = [
        {"$group": {"_id": "$Город"}},  # Группируем документы по полю "Город"
        {"$sort": {"_id": 1}}  # Сортируем результаты по городу
    ]
    cities = db.russianCities.aggregate(pipeline)
    # Извлекаем названия городов из результатов агрегации
    cities_list = sorted([city["_id"] for city in cities if city["_id"] is not None])
    return jsonify(cities_list)
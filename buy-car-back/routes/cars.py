from math import ceil
from app import app, db
from flask import jsonify, request
from bson import json_util, ObjectId
import json

@app.route('/cars', methods=['GET'])
def get_cars():
    user_id = request.args.get('userId', '')
    try:
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('pageSize', 10))
    except ValueError:
        return jsonify({'error': 'Некорректные параметры page или pageSize'}), 400

    # Получаем фильтры для конкретного пользователя
    filter_item = db.filter.find_one({'userId': user_id}) or {}

    # Формируем запрос на основе фильтров
    query = {}
    sort_criteria = []  # Список для критериев сортировки

    # Определение критериев сортировки
    if 'sorting' in filter_item:
        if filter_item['sorting'] == 'priceFromLow':
            sort_criteria.append(('price', 1))  # Сортировка по цене от меньшей к большей
        elif filter_item['sorting'] == 'priceFromHigh':
            sort_criteria.append(('price', -1))  # Сортировка по цене от большей к меньшей
        elif filter_item['sorting'] == 'dateFromNew':
            sort_criteria.append(('publishDate', -1))  # Сортировка по дате от новых к старым
        elif filter_item['sorting'] == 'dateFromOld':
            sort_criteria.append(('publishDate', 1))  # Сортировка по дате от старых к новым
        elif filter_item['sorting'] == 'mileageFromLow':
            sort_criteria.append(('mileage', 1))  # Сортировка по пробегу от меньшего к большему
        elif filter_item['sorting'] == 'mileageFromHigh':
            sort_criteria.append(('mileage', -1))  # Сортировка по пробегу от большего к меньшему

    # Добавляем фильтры по цене
    if 'priceMin' in filter_item and filter_item['priceMin'] is not None:
        query['price'] = {'$gte': filter_item['priceMin']}    
    if 'priceMax' in filter_item and filter_item['priceMax'] is not None:
        query.setdefault('price', {})['$lte'] = filter_item['priceMax']

    # Добавляем фильтры по пробегу
    if 'mileageMin' in filter_item and filter_item['mileageMin'] is not None:
        query['mileage'] = {'$gte': filter_item['mileageMin']}
    if 'mileageMax' in filter_item and filter_item['mileageMax'] is not None:
        query.setdefault('mileage', {})['$lte'] = filter_item['mileageMax']

    # Добавляем фильтры по году выпуска
    if 'yearMin' in filter_item and filter_item['yearMin'] is not None:
        query['year'] = {'$gte': filter_item['yearMin']}
    if 'yearMax' in filter_item and filter_item['yearMax'] is not None:
        query.setdefault('year', {})['$lte'] = filter_item['yearMax']

    # Добавляем фильтры по количеству владельцев
    if 'ownersCountMin' in filter_item and filter_item['ownersCountMin'] is not None:
        query['ownersCount'] = {'$gte': filter_item['ownersCountMin']}
    if 'ownersCountMax' in filter_item and filter_item['ownersCountMax'] is not None:
        query.setdefault('ownersCount', {})['$lte'] = filter_item['ownersCountMax']

    # Инициализируем фильтры марки и модели как пустой список
    brand_and_model_filters = []

    # Добавляем фильтр по марке
    if 'mark' in filter_item and filter_item['mark'] is not None and filter_item['mark'] != 'all':
        brand_and_model_filters.append({'name': {'$regex': filter_item['mark'], '$options': 'i'}})
    # Добавляем фильтр по модели
    if 'model' in filter_item and filter_item['model'] is not None and filter_item['model'] != 'all': 
        brand_and_model_filters.append({'name': {'$regex': filter_item['model'], '$options': 'i'}})
    # Если есть фильтры по марке или модели, добавляем их в запрос через $and
    if brand_and_model_filters:
        query['$and'] = brand_and_model_filters

    if 'settlement' in filter_item and filter_item['settlement'] is not None and filter_item['settlement'] != 'all':
        query['settlement'] = {'$regex': filter_item['settlement'], '$options': 'i'}

    if 'isShowroom' in filter_item and filter_item['isShowroom'] is not None and filter_item['isShowroom'] != 'all':
        query['isShowroom'] = filter_item['isShowroom'] == 'showroom'

    # Применение пагинации
    skip_amount = (page - 1) * page_size

    # Получаем общее количество записей до применения пагинации
    total_items = db.cars.count_documents(query)

    # Рассчитываем общее количество страниц
    total_pages = ceil(total_items / page_size)

    # Извлекаем и сортируем данные из базы данных
    if sort_criteria:
        items = db.cars.find(query).sort(sort_criteria).skip(skip_amount).limit(page_size)
    else:
        sort_criteria.append(('publishDate', -1))
        items = db.cars.find(query).sort(sort_criteria).skip(skip_amount).limit(page_size)

    result = []
    favorite_cars_ids = [favorite['carId'] for favorite in db.favoriteCars.find({"userId": user_id})]
    compared_cars_ids = [compared['carId'] for compared in db.comparedCars.find({"userId": user_id})]
   
    for item in items:
        is_favorite = str(item['_id']) in favorite_cars_ids
        is_compared = str(item['_id']) in compared_cars_ids
        
        car_data = {
            'id': str(item['_id']), 
            'name': item['name'], 
            'price': item['price'],
            'settlement': item['settlement'],
            'isShowroom': item['isShowroom'],
            'publishDate': item['publishDate'],
            'year': item['year'],
            'mileage': item['mileage'],
            'ownersCount': item['ownersCount'],
            'imageUrl': item['imageUrl'],
            'transmission': item['transmission'],
            'isFavorite': is_favorite, 
            'isCompared': is_compared,
            'hasDouble': item['hasDouble'],
            'diff': item['diff'],
            'isBroked': item['isBroked'],
            'url': item.get('url', None),
        }
        # if not (item['hasDouble'] == True & (item['mileage'] < 100000 | item['mileage'] > 200000)): result.append(car_data)
        result.append(car_data)

    return jsonify({
        'cars': result,
        'totalItems': total_items,
        'currentPage': page,
        'totalPages': total_pages,
        'pageSize': page_size,
    })


@app.route('/favorites', methods=['GET'])
def get_favorites():
    user_id = request.args.get('userId')

    if not user_id:
        return jsonify({'error': 'userId required'}), 400

    # Ищем все избранные автомобили текущего пользователя
    favorite_items = db.favoriteCars.find({'userId': user_id}).sort('_id', -1)
    result = []

    for item in favorite_items:
        car_id = item['carId'] 
        car = db.cars.find_one({'_id': ObjectId(car_id)})
        
        if car:  # Проверяем, найден ли автомобиль
            is_compared = str(car['_id']) in [compared['carId'] for compared in db.comparedCars.find({"userId": user_id})]
            
            car_data = {
                'id': str(car['_id']),
                'name': car['name'],
                'price': car['price'],
                'settlement': car['settlement'],
                'isShowroom': car['isShowroom'],
                'publishDate': car['publishDate'],
                'year': car['year'],
                'mileage': car['mileage'],
                'ownersCount': car['ownersCount'],
                'imageUrl': car['imageUrl'],
                'transmission': car['transmission'],
                'isFavorite': True,
                'isCompared': is_compared,
                'diff': car['diff'],
            }
            result.append(car_data)

    return jsonify(result)

@app.route('/compared', methods=['GET'])
def get_compared():
    user_id = request.args.get('userId')

    if not user_id:
        return jsonify({'error': 'userId required'}), 400

    # Ищем все избранные автомобили текущего пользователя
    compared_items = db.comparedCars.find({'userId': user_id}).sort('_id', -1)
    result = []

    for item in compared_items:
        car_id = item['carId']  
        car = db.cars.find_one({'_id': ObjectId(car_id)})
        
        if car:  # Проверяем, найден ли автомобиль
            is_favorite = str(car['_id']) in [favorite['carId'] for favorite in db.favoriteCars.find({"userId": user_id})]
            
            car_data = {
                'id': str(car['_id']),
                'name': car['name'],
                'price': car['price'],
                'settlement': car['settlement'],
                'isShowroom': car['isShowroom'],
                'publishDate': car['publishDate'],
                'year': car['year'],
                'mileage': car['mileage'],
                'ownersCount': car['ownersCount'],
                'imageUrl': car['imageUrl'],
                'transmission': car['transmission'],
                'isFavorite': is_favorite,
                'isCompared': True,
                'diff': car['diff'],
            }
            result.append(car_data)

    return jsonify(result)

@app.route('/cars/clickOnFavorite', methods=['PUT'])
def click_on_favorite():

    car_id = request.json['carId']
    user_id = request.json['userId']

    # Проверяем, существует ли уже такая запись в избранном
    favorite = db.favoriteCars.find_one({'carId': car_id, 'userId': user_id})
    
    if favorite:
        # Если существует, удаляем её
        db.favoriteCars.delete_one({'_id': favorite['_id']})
        return jsonify({'message': 'Removed from favorites'}), 200
    else:
        # Если не существует, добавляем новую запись
        db.favoriteCars.insert_one({'carId': car_id, 'userId': user_id})
        return jsonify({'message': 'Added to favorites'}), 201

@app.route('/cars/clickOnCompare', methods=['PUT'])
def click_on_compared():

    car_id = request.json['carId']
    user_id = request.json['userId']

    # Проверяем, существует ли уже такая запись в избранном
    compared = db.comparedCars.find_one({'carId': car_id, 'userId': user_id})
    
    if compared:
        # Если существует, удаляем её
        db.comparedCars.delete_one({'_id': compared['_id']})
        return jsonify({'message': 'Removed from compared'}), 200
    else:
        # Если не существует, добавляем новую запись
        db.comparedCars.insert_one({'carId': car_id, 'userId': user_id})
        return jsonify({'message': 'Added to compared'}), 201

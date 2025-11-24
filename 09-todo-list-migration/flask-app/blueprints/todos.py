"""
Todos Blueprint
待辦事項相關路由
"""
from flask import Blueprint, request, jsonify
from pydantic import ValidationError
from database import get_db
from repositories.todo_repository import TodoRepository
from services.todo_service import TodoService
from schemas.todo import TodoCreate, TodoUpdate
from utils.cache import CacheManager
from middleware.jwt_middleware import get_current_user_id
from core.exceptions import NotFoundException, BadRequestException

todos_bp = Blueprint('todos', __name__, url_prefix='/api/v1/todos')
cache_manager = CacheManager()


@todos_bp.route('', methods=['GET'])
def get_all_todos():
    """獲取用戶的所有 TODO"""
    try:
        user_id = get_current_user_id()
        
        db = next(get_db())
        try:
            todo_repo = TodoRepository(db)
            todo_service = TodoService(todo_repo, cache_manager)
            
            todos = todo_service.get_all_todos(user_id)
            return jsonify(todos), 200
        finally:
            db.close()
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@todos_bp.route('/<int:todo_id>', methods=['GET'])
def get_todo(todo_id: int):
    """獲取單個 TODO"""
    try:
        user_id = get_current_user_id()
        
        db = next(get_db())
        try:
            todo_repo = TodoRepository(db)
            todo_service = TodoService(todo_repo, cache_manager)
            
            todo = todo_service.get_todo(todo_id, user_id)
            return jsonify(todo), 200
        finally:
            db.close()
    except NotFoundException as e:
        return jsonify({"error": e.message}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@todos_bp.route('', methods=['POST'])
def create_todo():
    """創建新 TODO"""
    try:
        user_id = get_current_user_id()
        
        # 驗證請求資料
        data = request.get_json()
        todo_data = TodoCreate(**data)
        
        db = next(get_db())
        try:
            todo_repo = TodoRepository(db)
            todo_service = TodoService(todo_repo, cache_manager)
            
            todo = todo_service.create_todo(
                user_id=user_id,
                title=todo_data.title,
                description=todo_data.description
            )
            return jsonify(todo), 201
        finally:
            db.close()
    except ValidationError as e:
        return jsonify({"error": str(e)}), 422
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@todos_bp.route('/<int:todo_id>', methods=['PUT'])
def update_todo(todo_id: int):
    """更新 TODO"""
    try:
        user_id = get_current_user_id()
        
        # 驗證請求資料
        data = request.get_json()
        todo_data = TodoUpdate(**data)
        
        db = next(get_db())
        try:
            todo_repo = TodoRepository(db)
            todo_service = TodoService(todo_repo, cache_manager)
            
            todo = todo_service.update_todo(
                todo_id=todo_id,
                user_id=user_id,
                title=todo_data.title,
                description=todo_data.description,
                completed=todo_data.completed
            )
            return jsonify(todo), 200
        finally:
            db.close()
    except ValidationError as e:
        return jsonify({"error": str(e)}), 422
    except NotFoundException as e:
        return jsonify({"error": e.message}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@todos_bp.route('/<int:todo_id>', methods=['DELETE'])
def delete_todo(todo_id: int):
    """刪除 TODO"""
    try:
        user_id = get_current_user_id()
        
        db = next(get_db())
        try:
            todo_repo = TodoRepository(db)
            todo_service = TodoService(todo_repo, cache_manager)
            
            todo_service.delete_todo(todo_id, user_id)
            return jsonify({"message": "Todo deleted successfully"}), 200
        finally:
            db.close()
    except NotFoundException as e:
        return jsonify({"error": e.message}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


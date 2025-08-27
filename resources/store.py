import uuid

from flask import request
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from flask_jwt_extended import jwt_required
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from schemas import StoreSchema, PaginatedStoreSchema

from db import db
from models import StoreModel

blp = Blueprint("stores", __name__, description="Operations on Stores")

@blp.route("/store/<int:store_id>")
class Store(MethodView):
    @jwt_required()
    @blp.response(200, StoreSchema)
    def get(self, store_id):
        store = StoreModel.query.get_or_404(store_id)
        return store

    @jwt_required()
    def delete(self, store_id):
        store = StoreModel.query.get_or_404(store_id)
        db.session.delete(store)
        db.session.commit()
        return {"message": "Store deleted."}


@blp.route("/store")
class StoreList(MethodView):
    @jwt_required()
    @blp.response(200, PaginatedStoreSchema)
    def get(self):
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 10, type=int)
        q = request.args.get("q", "", type=str)

        query = StoreModel.query
        if q:
            query = query.filter(StoreModel.name.ilike(f"%{q}%"))
        
        p = query.order_by(StoreModel.id.asc()).paginate(page=page, per_page=per_page, error_out=False)


        payload = {
            "items": p.items,
            "page": p.page,
            "per_page": p.per_page,
            "total": p.total,
            "pages": p.pages,  # Calculate total pages
        }

        from schemas import PaginatedStoreSchema
        return PaginatedStoreSchema().dump(payload)

    @jwt_required()
    @blp.arguments(StoreSchema)
    @blp.response(201, StoreSchema)
    def post(self, store_data):
        store = StoreModel(**store_data)

        try:
            db.session.add(store)
            db.session.commit()
        except IntegrityError:
            abort(400, message="A store with that name already exists.")
        except SQLAlchemyError:
            abort(500, message="An error occurred while creating the store.")

        return store
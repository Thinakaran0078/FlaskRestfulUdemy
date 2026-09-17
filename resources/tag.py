from flask.views import MethodView
from flask_smorest import Blueprint, abort
from flask_jwt_extended import jwt_required
from sqlalchemy.exc import SQLAlchemyError

from db import db
from models import TagModel, StoreModel, ItemModel
from schemas import TagSchema, TagandItemSchema

blp = Blueprint("tags", __name__, description="Operations on Tags")

@blp.route("/store/<int:store_id>/tag")
class TagInStore(MethodView):
    @jwt_required()
    @blp.response(200, TagSchema(many=True))
    def get(self, store_id):
        store = db.session.get(StoreModel, store_id)
        if store is None:
            abort(404, message="Store not found.")

        return store.tags.all()

    @jwt_required()
    @blp.arguments(TagSchema)
    @blp.response(201, TagSchema)
    def post(self, tag_data, store_id):
        store = db.session.get(StoreModel, store_id)
        if store is None:
            abort(404, message="Store not found.")
        tag = TagModel(**tag_data, store_id=store_id)

        try:
            db.session.add(tag)
            db.session.commit()
        except SQLAlchemyError as e:
            abort(500, message=str(e))

        return tag
    
@blp.route("/item/<int:item_id>/tag/<int:tag_id>")
class LinkTagsToItem(MethodView):
    @jwt_required()
    @blp.response(201, TagSchema)
    def post(self, item_id, tag_id):
        item = db.session.get(ItemModel, item_id)
        if item is None:
            abort(404, message="Item not found.")
        tag = db.session.get(TagModel, tag_id)
        if tag is None:
            abort(404, message="Tag not found.")

        item.tags.append(tag)
        try:
            db.session.add(item)
            db.session.commit()
        except SQLAlchemyError:
            abort(500, message="An error occurred while linking the tag to the item.")

        return tag

    @jwt_required()
    @blp.response(200, TagandItemSchema)
    def delete(self, item_id, tag_id):
        item = db.session.get(ItemModel, item_id)
        if item is None:
            abort(404, message="Item not found.")
        tag = db.session.get(TagModel, tag_id)
        if tag is None:
            abort(404, message="Tag not found.")

        item.tags.remove(tag)
        try:
            db.session.add(item)
            db.session.commit()
        except SQLAlchemyError:
            abort(500, message="An error occurred while removing the tag from the item.")

        return {"message": "Item removed from Tag", "item": item, "tag": tag}


@blp.route("/tag/<int:tag_id>")
class Tag(MethodView):
    @jwt_required()
    @blp.response(200, TagSchema)
    def get(self, tag_id):
        tag = db.session.get(TagModel, tag_id)
        if tag is None:
            abort(404, message="Tag not found.")
        return tag

    @jwt_required()
    @blp.response(
        202,
        description="Deletes a tag if no item is tagged with it.",
        example={"message": "Tag deleted."}
    )
    @blp.alt_response(404, description="Tag not found.")
    @blp.alt_response(
        400,
        description="Returned if the tag is assigned to one or more items. In this case, the tag is not deleted.",
    )
    def delete(self, tag_id):
        tag = db.session.get(TagModel, tag_id)
        if tag is None:
            abort(404, message="Tag not found.")

        if tag.items:
            abort(400, message="Tag is assigned to one or more items and cannot be deleted.")

        db.session.delete(tag)
        db.session.commit()
        return {"message": "Tag deleted."}
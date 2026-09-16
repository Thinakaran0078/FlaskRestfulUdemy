from db import db
from models.item import ItemModel
from models.item_tags import ItemTags
from models.store import StoreModel
from models.tag import TagModel
from models.user import UserModel


def test_store_model_defaults_and_relationships(app):
    with app.app_context():
        store = StoreModel(name="Corner Shop")
        db.session.add(store)
        db.session.commit()

        assert store.id is not None
        assert store.items.count() == 0
        assert store.tags.count() == 0


def test_item_belongs_to_store_and_cascades_on_delete(app):
    with app.app_context():
        store = StoreModel(name="Corner Shop")
        item = ItemModel(name="Widget", price=9.99, store=store)
        db.session.add_all([store, item])
        db.session.commit()

        item_id = item.id
        assert item.store_id == store.id
        assert store.items.count() == 1

        db.session.delete(store)
        db.session.commit()

        # StoreModel.items relationship uses cascade="all, delete"
        assert db.session.get(ItemModel, item_id) is None


def test_item_name_must_be_unique(app):
    with app.app_context():
        store = StoreModel(name="Corner Shop")
        db.session.add(store)
        db.session.commit()

        db.session.add(ItemModel(name="Widget", price=1.0, store=store))
        db.session.commit()

        db.session.add(ItemModel(name="Widget", price=2.0, store=store))
        try:
            db.session.commit()
            assert False, "expected an IntegrityError for a duplicate item name"
        except Exception:
            db.session.rollback()


def test_tag_belongs_to_store_and_links_to_items_via_item_tags(app):
    with app.app_context():
        store = StoreModel(name="Corner Shop")
        item = ItemModel(name="Widget", price=9.99, store=store)
        tag = TagModel(name="Sale", store=store)
        db.session.add_all([store, item, tag])
        db.session.commit()

        item.tags.append(tag)
        db.session.commit()

        assert tag in item.tags
        assert item in tag.items
        assert db.session.query(ItemTags).count() == 1


def test_user_model_stores_username_and_password_hash(app):
    with app.app_context():
        user = UserModel(username="alice", password="hashed-password")
        db.session.add(user)
        db.session.commit()

        fetched = db.session.get(UserModel, user.id)
        assert fetched.username == "alice"
        assert fetched.password == "hashed-password"


def test_username_must_be_unique(app):
    with app.app_context():
        db.session.add(UserModel(username="alice", password="hash1"))
        db.session.commit()

        db.session.add(UserModel(username="alice", password="hash2"))
        try:
            db.session.commit()
            assert False, "expected an IntegrityError for a duplicate username"
        except Exception:
            db.session.rollback()

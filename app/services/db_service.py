from app import db
from app.models.ad_asset import AdAsset
from app.models.ad import Ad

class DBService:
    @staticmethod
    def save_to_db(item):
        """
        Save an item to the database
        """
        try:
            db.session.add(item)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Error saving to database: {str(e)}")
            return False

    @staticmethod
    def delete_from_db(item):
        """
        Delete an item from the database
        """
        try:
            db.session.delete(item)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Error deleting from database: {str(e)}")
            return False

    @staticmethod
    def get_ad_asset_by_id(asset_id):
        """
        Get an ad asset by its ID
        """
        return AdAsset.query.get(asset_id)

    @staticmethod
    def get_ad_by_id(ad_id):
        """
        Get an ad by its ID
        """
        return Ad.query.get(ad_id)

    @staticmethod
    def update_ad_asset(asset_id, updates):
        """
        Update an ad asset with the given updates
        """
        try:
            asset = AdAsset.query.get(asset_id)
            if asset:
                for key, value in updates.items():
                    setattr(asset, key, value)
                db.session.commit()
                return True
            return False
        except Exception as e:
            db.session.rollback()
            print(f"Error updating ad asset: {str(e)}")
            return False 
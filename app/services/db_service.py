from app import db
from app.models.image_data import ImageData

class DatabaseService:
    @staticmethod
    def save_image_data(filename, s3_path, analysis_result):
        try:
            image_data = ImageData(
                filename=filename,
                s3_path=s3_path,
                analysis_result=analysis_result
            )
            db.session.add(image_data)
            db.session.commit()
            return image_data
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Failed to save to database: {str(e)}")

    @staticmethod
    def generate_report():
        try:
            images = ImageData.query.all()
            return [image.to_dict() for image in images]
        except Exception as e:
            raise Exception(f"Failed to generate report: {str(e)}") 
from database import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)
    created_at = db.Column(
        db.DateTime,
        server_default=db.func.current_timestamp()
    )


class Medicine(db.Model):
    __tablename__ = "medicines"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    medicine_name = db.Column(db.String(150), nullable=False)
    composition = db.Column(db.String(255), nullable=False)
    manufacturer = db.Column(db.String(150))
    price = db.Column(db.Numeric(10, 2), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(
        db.DateTime,
        server_default=db.func.current_timestamp()
    )


class MedicineSearchHistory(db.Model):
    __tablename__ = "medicine_search_history"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    medicine_name = db.Column(db.String(150), nullable=False)
    searched_at = db.Column(
        db.DateTime,
        server_default=db.func.current_timestamp()
    )


class UserMedication(db.Model):
    __tablename__ = "user_medications"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    medicine_id = db.Column(
        db.Integer,
        db.ForeignKey("medicines.id", ondelete="CASCADE"),
        nullable=False
    )
    dosage = db.Column(db.String(100))
    frequency = db.Column(db.String(100))
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    created_at = db.Column(
        db.DateTime,
        server_default=db.func.current_timestamp()
    )


class MedicineReminder(db.Model):
    __tablename__ = "medicine_reminders"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_medication_id = db.Column(
        db.Integer,
        db.ForeignKey("user_medications.id", ondelete="CASCADE"),
        nullable=False
    )
    reminder_date = db.Column(db.Date, nullable=False)
    reminder_time = db.Column(db.Time, nullable=False)
    status = db.Column(
        db.String(20),
        default="pending"
    )
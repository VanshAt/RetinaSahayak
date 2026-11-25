import logging
from sqlalchemy.orm import Session, sessionmaker
from backend.app.core.database import SessionLocal, engine, Base
from backend.app.core.security import get_password_hash
from backend.app.models.health_center import HealthCenter
from backend.app.models.user import User
from backend.app.models.patient import Patient

logger = logging.getLogger("RetinaSahayak.Seeder")


def seed_database(target_engine=None):
    """Seeds database with demo health centers, users, and anonymized patients."""
    eng = target_engine or engine
    Base.metadata.create_all(bind=eng)
    session_factory = sessionmaker(bind=eng)
    db: Session = session_factory()

    try:
        # 1. Seed Health Centers
        hc1 = db.query(HealthCenter).filter(HealthCenter.id == "hc_ramnagar_01").first()
        if not hc1:
            hc1 = HealthCenter(
                id="hc_ramnagar_01",
                name="Ramnagar Primary Health Centre",
                facility_code="PHC-UP-VNS-01",
                district="Varanasi",
                state="Uttar Pradesh",
                connectivity_tier="TIER_3"
            )
            db.add(hc1)

        hc2 = db.query(HealthCenter).filter(HealthCenter.id == "hc_chiraigaon_02").first()
        if not hc2:
            hc2 = HealthCenter(
                id="hc_chiraigaon_02",
                name="Chiraigaon Community Health Centre",
                facility_code="CHC-UP-VNS-02",
                district="Varanasi",
                state="Uttar Pradesh",
                connectivity_tier="TIER_2"
            )
            db.add(hc2)

        db.commit()

        # 2. Seed Users
        users_to_seed = [
            {
                "email": "admin@retinasahayak.in",
                "password": "AdminDemo123!",
                "full_name": "Varanasi District Health Admin",
                "role": "ADMIN",
                "health_center_id": None,
                "medical_reg": None
            },
            {
                "email": "worker.ramnagar@retinasahayak.in",
                "password": "WorkerDemo123!",
                "full_name": "Smt. Sunita Devi (ANM)",
                "role": "PHC_WORKER",
                "health_center_id": "hc_ramnagar_01",
                "medical_reg": None
            },
            {
                "email": "worker.chiraigaon@retinasahayak.in",
                "password": "WorkerDemo123!",
                "full_name": "Smt. Pushpa Yadav (ASHA)",
                "role": "PHC_WORKER",
                "health_center_id": "hc_chiraigaon_02",
                "medical_reg": None
            },
            {
                "email": "dr.verma@retinasahayak.in",
                "password": "DoctorDemo123!",
                "full_name": "Dr. Rajesh Verma, MD (Ophthal)",
                "role": "OPHTHALMOLOGIST",
                "health_center_id": None,
                "medical_reg": "MCI-UP-48821"
            },
            {
                "email": "dr.sharma@retinasahayak.in",
                "password": "DoctorDemo123!",
                "full_name": "Dr. Neha Sharma, MS (Retina)",
                "role": "OPHTHALMOLOGIST",
                "health_center_id": None,
                "medical_reg": "MCI-UP-52190"
            }
        ]

        for u in users_to_seed:
            existing = db.query(User).filter(User.email == u["email"].lower()).first()
            if not existing:
                new_u = User(
                    email=u["email"].lower(),
                    hashed_password=get_password_hash(u["password"]),
                    full_name=u["full_name"],
                    role=u["role"],
                    health_center_id=u["health_center_id"],
                    medical_registration_no=u["medical_reg"],
                    is_active=True
                )
                db.add(new_u)

        db.commit()

        # 3. Seed 10 Anonymized Patients
        patients_to_seed = [
            {"code": "PAT-VNS-1001", "age_group": "51-65", "gender": "MALE", "dm_years": 12, "htn": True, "loc": "Ramnagar Village", "hc": "hc_ramnagar_01"},
            {"code": "PAT-VNS-1002", "age_group": "36-50", "gender": "FEMALE", "dm_years": 4, "htn": False, "loc": "Chiraigaon North", "hc": "hc_chiraigaon_02"},
            {"code": "PAT-VNS-1003", "age_group": "65+", "gender": "MALE", "dm_years": 18, "htn": True, "loc": "Mughalsarai Border", "hc": "hc_ramnagar_01"},
            {"code": "PAT-VNS-1004", "age_group": "51-65", "gender": "FEMALE", "dm_years": 8, "htn": True, "loc": "Shivpur Basti", "hc": "hc_chiraigaon_02"},
            {"code": "PAT-VNS-1005", "age_group": "18-35", "gender": "FEMALE", "dm_years": 2, "htn": False, "loc": "Ramnagar Ghat", "hc": "hc_ramnagar_01"},
            {"code": "PAT-VNS-1006", "age_group": "51-65", "gender": "MALE", "dm_years": 15, "htn": True, "loc": "Ashapur Kalan", "hc": "hc_chiraigaon_02"},
            {"code": "PAT-VNS-1007", "age_group": "36-50", "gender": "MALE", "dm_years": 6, "htn": False, "loc": "Chitaipur", "hc": "hc_ramnagar_01"},
            {"code": "PAT-VNS-1008", "age_group": "65+", "gender": "FEMALE", "dm_years": 22, "htn": True, "loc": "Sarnath Rural", "hc": "hc_chiraigaon_02"},
            {"code": "PAT-VNS-1009", "age_group": "51-65", "gender": "FEMALE", "dm_years": 9, "htn": False, "loc": "Kotwa Village", "hc": "hc_ramnagar_01"},
            {"code": "PAT-VNS-1010", "age_group": "36-50", "gender": "MALE", "dm_years": 5, "htn": True, "loc": "Sindhora Road", "hc": "hc_chiraigaon_02"},
        ]

        for p in patients_to_seed:
            existing_p = db.query(Patient).filter(Patient.patient_code == p["code"]).first()
            if not existing_p:
                new_p = Patient(
                    patient_code=p["code"],
                    age_group=p["age_group"],
                    gender=p["gender"],
                    diabetes_duration_years=p["dm_years"],
                    known_hypertension=p["htn"],
                    phc_location=p["loc"],
                    health_center_id=p["hc"]
                )
                db.add(new_p)

        db.commit()
        logger.info("Demo database seed complete: 2 Health Centers, 5 Users, 10 Anonymized Patients.")
    except Exception as e:
        db.rollback()
        logger.error(f"Error seeding database: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()

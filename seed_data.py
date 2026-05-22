"""
Seed the database with realistic sample data for demo purposes.
Run: python seed_data.py
"""
import os
import random
from datetime import datetime, timedelta
from app import app
from database import db, Order, init_db
from auth import login_manager
from generate_logo import generate_logo
from qr_generator import generate_all_qr_codes

login_manager.init_app(app)
init_db(app)

ALGERIAN_PHONES = [
    "0555123456", "0660123457", "0777123458", "0555987654",
    "0661876543", "0777654321", "0555345678", "0660987123",
    "0777345678", "0555765432", "0660543210", "0777888999",
    "0555001122", "0660334455", "0777667788", "0555998877",
    "0660554433", "0777221100", "0555667788", "0660998877",
]

FILE_NAMES = [
    "CV_2024.pdf", "contrat_location.docx", "photo_identite.jpg",
    "attestation_scolaire.pdf", "facture_eau.pdf", "diplome.pdf",
    "carte_etudiant.jpg", "rapport_stage.pdf", "devis_travaux.xlsx",
    "lettre_motivation.pdf", "plan_maison.pdf", "catalogue.jpg",
    "bon_commande.xlsx", "certificat_medical.pdf", "menu_restaurant.pdf",
    "affiche_promo.pdf", "flyer_evenement.pdf", "extrait_naissance.pdf",
    "contrat_travail.docx", "carte_visite.pdf"
]

COMPUTERS = ["PC1", "PC2", "PC3", "PC4"]
STATUSES = ["new", "printing", "done", "transferred"]

def seed():
    with app.app_context():
        existing = Order.query.count()
        if existing > 5:
            print(f"Database already has {existing} orders. Skipping seed.")
            return

        print("Seeding 50 sample orders...")
        now = datetime.utcnow()

        for i in range(50):
            days_ago = random.randint(0, 29)
            hours_ago = random.randint(7, 23)
            minutes = random.randint(0, 59)
            created = now - timedelta(days=days_ago, hours=hours_ago, minutes=minutes)

            computer_id = random.choice(COMPUTERS)
            color_mode = random.choices(['bw', 'color'], weights=[0.65, 0.35])[0]
            paper_size = random.choice(['A4', 'A3', 'A4', 'A4'])
            copies = random.randint(1, 15)

            if paper_size == 'A3':
                price = copies * (30 if color_mode == 'color' else 10) * 2
            else:
                price = copies * (30 if color_mode == 'color' else 10)

            status = random.choices(
                STATUSES,
                weights=[0.2, 0.15, 0.5, 0.15]
            )[0]

            order = Order(
                order_number=f"2024{random.randint(1,12):02d}{random.randint(1,28):02d}-{1000+i:04d}",
                computer_id=computer_id,
                customer_phone=random.choice(ALGERIAN_PHONES),
                file_path=f"uploads/sample_{i}.pdf",
                file_name=random.choice(FILE_NAMES),
                file_type="pdf",
                copies=copies,
                color_mode=color_mode,
                paper_size=paper_size,
                notes="" if random.random() > 0.5 else "طباعة وجهين" if random.random() > 0.5 else "تدبيس",
                status=status,
                price=float(price),
                page_count=random.randint(1, 20),
                created_at=created,
                updated_at=created + timedelta(minutes=random.randint(1, 120))
            )
            db.session.add(order)

        db.session.commit()
        print(f"  Created 50 sample orders.")

        generate_logo()
        generate_all_qr_codes()
        print("  Logo and QR codes generated.")
        print("Seed complete!")


if __name__ == '__main__':
    seed()

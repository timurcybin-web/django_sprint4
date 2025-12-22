python -m venv venv
source venv/Scripts/activate
pip install -r requirements.txt
cd blogicum
python manage.py migrate

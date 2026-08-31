from setuptools import setup, find_packages

setup(
    name="booksea",
    version="1.0.0",
    description="BookSea - Digital Library with PDF to Audio conversion",
    author="Vathanaruban Shayarukshan",
    url="https://github.com/VathanarubanShayarukshan/Book-sea",
    py_modules=["cli", "run"],
    include_package_data=True,
    install_requires=[
        "Flask==3.0.0",
        "Flask-SQLAlchemy==3.1.1",
        "Flask-Login==0.6.3",
        "Flask-WTF==1.2.1",
        "WTForms==3.1.1",
        "bcrypt==4.1.2",
        "gTTS==2.5.0",
        "PyPDF2==3.0.1",
        "deep-translator==1.11.4",
        "PyMuPDF==1.23.7",
        "Werkzeug==3.0.1",
        "python-dotenv==1.0.0",
        "Pillow==10.1.0",
        "mutagen==1.47.0",
    ],
    entry_points={
        "console_scripts": [
            "booksea=cli:main",
        ],
    },
    python_requires=">=3.8",
)

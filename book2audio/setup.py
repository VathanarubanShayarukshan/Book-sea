from setuptools import setup, find_packages

setup(
    name="book2audio",
    version="1.0.0",
    author="book2audio",
    description="Convert any text format books to audio files",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/username/book2audio",
    py_modules=["book2audio"],
    install_requires=[
        "gTTS",
        "langdetect",
        "beautifulsoup4",
        "python-docx",
        "markdown",
        "odfpy",
        "pydub",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    entry_points={
        "console_scripts": [
            "book2audio=book2audio:main",
        ],
    },
)

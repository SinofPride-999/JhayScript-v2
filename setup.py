from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="jhayscript",
    version="1.0.0",
    author="Jhay",
    author_email="jhaycodes999@email.com",
    description="JhayScript - A custom scripting language",
    long_description=long_description,
    long_description_content_type="text/markdown",
    # url="https://github.com/yourusername/jhayscript",
    packages=find_packages(),
    package_data={
        'jhayscript': ['*.jhay'],  # Include any example script files
    },
    entry_points={
        'console_scripts': [
            'jhayscript=jhayscript.__main__:main',
            'jhay=jhayscript.__main__:main'  # Optional shorter alias
        ],
    },
    python_requires='>=3.6',
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    keywords="scripting language interpreter",
    
)
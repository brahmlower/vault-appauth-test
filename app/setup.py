from setuptools import setup

setup(
    name = 'app',
    version = '0.1.0',
    description = 'A test service',
    author = 'Brahm Lower',
    author_email = 'bplower@gmail.com',

    py_modules = ["app"],
    install_requires = [
        'Flask',
        'PyYAML',
        'psycopg2-binary',
        'hvac'
    ],
    entry_points = {
        'console_scripts': [
            'app=app:main'
        ]
    }
)
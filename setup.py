from setuptools import setup, find_packages

setup(
    name='Plex-Service',
    version='0.1',
    packages=find_packages(),
    py_modules=['download'],
    install_requires=[
        'libtorrent',
    ],
    entry_points={
        'console_scripts': [
            'download=download:main',
        ],
    },
    author='Votre Nom',
    author_email='votre.email@example.com',
    description='Un script de téléchargement utilisant libtorrent',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)